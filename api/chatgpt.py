import asyncio
import json
import os
import time
import hashlib
from datetime import datetime

import diskcache
from openai import OpenAI, AsyncOpenAI, OpenAIError
import dotenv
dotenv.load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
aclient = AsyncOpenAI()


logs_dir = os.path.join(os.getcwd(), '.chatgpt_history/logs')
cache_dir = os.path.join(os.getcwd(), '.chatgpt_history/cache')
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)

cache = diskcache.Cache(cache_dir)


def get_key(messages, model, **kwargs):
    key_data = {
        'messages': messages,
        'model': model
    }
    # Include other relevant parameters in the key
    for param in ['temperature', 'max_tokens', 'n', 'stop', 'presence_penalty', 'frequency_penalty']:
        if param in kwargs:
            key_data[param] = kwargs[param]

    return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()


def retry_on_exception(retries=5, initial_wait_time=1):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                wait_time = initial_wait_time
                for attempt in range(retries):
                    try:
                        return await func(*args, **kwargs)
                    except OpenAIError as e:
                        if attempt == retries - 1:
                            raise e
                        print(e)
                        await asyncio.sleep(wait_time)
                        wait_time *= 2
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                wait_time = initial_wait_time
                for attempt in range(retries):
                    try:
                        return func(*args, **kwargs)
                    except OpenAIError as e:
                        if attempt == retries - 1:
                            raise e
                        print(e)
                        time.sleep(wait_time)
                        wait_time *= 2
            return sync_wrapper
    return decorator


@retry_on_exception()
def complete(messages=None, model='gpt-4-turbo-preview', temperature=0, use_cache=True, **kwargs):
    if use_cache:
        key = get_key(messages, model, **kwargs)
        if key in cache:
            return cache.get(key)
    response = client.chat.completions.create(
        messages=messages, model=model, temperature=temperature, **kwargs)
    return parse_response(response, messages, model=model, **kwargs)


@retry_on_exception()
async def acomplete(messages=None, model='gpt-4-turbo-preview', temperature=0, use_cache=True, **kwargs):
    # make this work for streaming only basically
    assert kwargs.get('stream', False) == True
    if use_cache:
        key = get_key(messages, model, **kwargs)
        if key in cache:
            yield cache.get(key)
    response = await aclient.chat.completions.create(messages=messages,
                                                     model=model,
                                                     temperature=temperature,
                                                     **kwargs)
    async for item in parse_stream(response, messages, model=model, **kwargs):
        yield item


def parse_response(response, messages, model, **kwargs):
    n = kwargs.get('n', 1)
    stream = kwargs.get('stream', False)
    if stream:
        strm = parse_stream(response, messages, model=model, n=n)
        print(strm)
        print(type(strm))
        return strm

    results = []
    for choice in response.choices:
        message = choice.message
        if message.function_call:
            name = message.function_call.name
            try:
                args = json.loads(message.function_call.arguments)
            except json.decoder.JSONDecodeError as e:
                print('ERROR: OpenAI returned invalid JSON for function call arguments')
                raise e
            results.append({'role': 'function', 'name': name, 'args': args})
            log_completion(messages + [results[-1]], model=model)
        else:
            results.append(message.content)
            log_completion(messages + [message], model=model)

    output = results if n > 1 else results[0]
    cache.set(get_key(messages, model, **kwargs), output)
    return output


async def parse_stream(response, messages, model, **kwargs):
    n = kwargs.get('n', 1)
    results = ['' for _ in range(n)]
    async for chunk in response:
        for choice in chunk.choices:
            if not choice.delta:
                continue
            text = choice.delta.content
            if not text:
                continue
            idx = choice.index
            results[idx] += text
            if n == 1:
                yield text
            else:
                yield (text, idx)

    for r in results:
        log_completion(messages + [{'role': 'assistant', 'content': r}], model=model)
    cache.set(get_key(messages, model, **kwargs), results)


def log_completion(messages, model):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')

    save_path = os.path.join(logs_dir, timestamp + '.txt')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    log = ""
    for message in messages:
        if not isinstance(message, dict):
            message = dict(message)
            message = {k: v for k, v in message.items() if v is not None}

        log += message['role'].upper() + ' ' + '-'*100 + '\n\n'
        if 'name' in message:
            log += f"Called function: {message['name']}("
            if 'args' in message:
                log += '\n'
                for k, v in message['args'].items():
                    log += f"\t{k}={repr(v)},\n"
            log += ')'
            if 'content' in message:
                log += '\nContent:\n' + message['content']
        elif 'function_call' in message:
            log += f"Called function: {message['function_call'].get('name', 'UNKNOWN')}(\n"
            log += ')'
        else:
            log += message["content"]
        log += '\n\n'

    with open(save_path, 'w') as f:
        f.write(log)
