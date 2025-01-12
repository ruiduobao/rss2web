import openai
import json

def test_ai_translation():
    # 配置 OpenAI
    openai.api_key = "sk-LsJwuRBc4eikc3Ir002fD6B9F89349E3A65258650a88F3F6"  # 替换为你的 API key
    openai.base_url = "https://api.gpt.ge/v1/"
    
    try:
        # 测试文本
        test_title = "Accelerating CO2 Outgassing in the Equatorial Pacific from Satellite Remote Sensing"
        test_abstract = "This is a test abstract for translation verification."
        
        # 构建提示
        prompt = f"""请将以下英文标题和摘要翻译成中文：
        
        标题：{test_title}
        摘要：{test_abstract}
        
        请按以下格式返回JSON：
        {{
            "title": "中文标题",
            "abstract": "中文摘要"
        }}"""
        
        # 发送请求
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # 获取响应
        response = completion.choices[0].message.content
        
        # 尝试解析 JSON
        try:
            translation = json.loads(response)
            print("AI 模型测试成功！")
            print("\n翻译结果：")
            print(f"标题：{translation['title']}")
            print(f"摘要：{translation['abstract']}")
            return True
        except json.JSONDecodeError:
            print("警告：返回格式不是有效的 JSON")
            print("原始响应：", response)
            return False
            
    except Exception as e:
        print(f"错误：{str(e)}")
        return False

if __name__ == "__main__":
    test_ai_translation() 