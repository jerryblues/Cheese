import edge_tts
import asyncio
import aiofiles


async def read_text_file(file_path):
    """异步读取文本文件内容"""
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        return await f.read()


async def text_to_speech(text, voice, rate, volume, output):
    """将文本转换为语音并保存到文件"""
    try:
        print("start...")
        tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
        await tts.save(output)
        print("done...")
    except Exception as e:
        print(f"error... {e}")


async def my_function(text_file, voice, rate, volume, output):
    try:
        # 读取文本文件内容
        text = await read_text_file(text_file)
        print(text)
        # 执行文本到语音转换
        await text_to_speech(text, voice, rate, volume, output)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    text_file = "C:\\N-20W1PF3T3YXB-Data\\h4zhang\\Downloads\\TTS\\input.txt"
    voice = 'zh-CN-YunxiNeural'
    rate = '-4%'
    volume = '+0%'
    output = "C:\\N-20W1PF3T3YXB-Data\\h4zhang\\Downloads\\TTS\\audio.mp3"
    asyncio.run(my_function(text_file, voice, rate, volume, output))
