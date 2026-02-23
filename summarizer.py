import asyncio
import aiohttp
import tiktoken
import config

try:
    enc = tiktoken.get_encoding("cl100k_base")
except Exception:
    enc = None

def get_token_count(text: str) -> int:
    if enc:
        return len(enc.encode(text, disallowed_special=()))
    # Fallback heuristic: 1 token ~= 1-2 Chinese chars, let's be safe and say 1 char = 1 token
    return len(text)

async def summarize_chunk(session: aiohttp.ClientSession, chunk: str, character_name: str, is_final: bool = False) -> str:
    """
    Call the OpenAI API to summarize a chunk.
    """
    sys_prompt = f"你是一个个人记忆整理助手。请以第三人称客观视角（例如：'{character_name}这个月做了……'），将以下收集到的杂乱日记和记忆碎片进行归纳提炼。要求：1. 简明扼要，按照逻辑串联。2. 提取出所有核心事件，不遗漏重要信息。3. 纯文本或简单Markdown排版，无需过渡性废话。"
    if is_final:
        sys_prompt = f"你是一个个人记忆整理助手。以下是分段总结后的{character_name}的本月部分记忆流。请将它们整合成一个连贯、完整的本月整体总结报告，以第三人称视角表述（例如：'{character_name}这个月……'）。涵盖全部核心事件，不遗漏。"

    headers = {
        "Authorization": f"Bearer {config.SUMMARY_MODEL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.SUMMARY_MODEL_NAME,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"记忆内容如下：\n{chunk}"}
        ],
        "temperature": 0.5
    }
    
    max_retries = 5
    base_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            async with session.post(config.SUMMARY_MODEL_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"API Error: {e}. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(delay)
            else:
                print(f"API Error: {e}. Max retries reached.")
                return f"[Summarization Error: Max retries reached after {max_retries} attempts - {e}]"

def chunk_memories(memories: list, max_tokens: int) -> list:
    chunks = []
    current_chunk = []
    current_count = 0
    
    for memory in memories:
        count = get_token_count(memory)
        if current_count + count > max_tokens and current_chunk:
            chunks.append("\n\n---\n\n".join(current_chunk))
            current_chunk = [memory]
            current_count = count
        else:
            current_chunk.append(memory)
            current_count += count
            
    if current_chunk:
        chunks.append("\n\n---\n\n".join(current_chunk))
        
    return chunks

async def process_month(memories: list, character_name: str, update_status_cb=None) -> str:
    """
    Summarize memories for a single month.
    """
    # Safe limit: 80% of max context to leave room for output and prompt
    max_tokens = int(config.SUMMARY_MODEL_MAX_CONTEXT * 0.8)
    
    chunks = chunk_memories(memories, max_tokens)
    
    if update_status_cb:
        update_status_cb(f"内存切分: {len(chunks)} 块")
    
    async with aiohttp.ClientSession() as session:
        if len(chunks) == 1:
            # Single API call
            return await summarize_chunk(session, chunks[0], character_name, is_final=False)
        else:
            # Concurrent API calls constrained by MAX_CONCURRENT_TASKS
            sem = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)
            async def bounded_summarize(c):
                async with sem:
                    return await summarize_chunk(session, c, character_name, is_final=False)
                    
            tasks = [bounded_summarize(c) for c in chunks]
            sub_summaries = await asyncio.gather(*tasks)
            
            if update_status_cb:
                update_status_cb("正在合并分块总结...")
                
            combined = "\n\n=== 分块边界 ===\n\n".join(sub_summaries)
            # Second pass
            return await summarize_chunk(session, combined, character_name, is_final=True)
