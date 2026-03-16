import requests
import json
import sys

# ==================== Configuration Parameters ====================
# Qwen API Configuration
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
API_KEY = ""
MODEL_NAME = ""
ENABLE_WEB_SEARCH = True  # Enable web search functionality
ENABLE_STREAM = True  # Enable stream output
ENABLE_DEEP_THINKING = True  # Enable deep thinking mode
# ==================================================


def ask_question(question, conversation_history=None, enable_search=True, enable_stream=True, enable_thinking=True):
    """
    Call Qwen model for text conversation with optional web search, stream output and deep thinking support
    
    Args:
        question: User's input question
        conversation_history: Conversation history (optional), format: [{"role": "user", "content": "..."}, ...]
        enable_search: Whether to enable web search functionality
        enable_stream: Whether to enable stream output
        enable_thinking: Whether to enable deep thinking mode
    
    Returns:
        Model's reply content (full text for non-stream, None for stream mode)
    """
    # Set request headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build message list
    messages = []
    
    # Add conversation history if exists
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user question
    messages.append({
        "role": "user",
        "content": question
    })
    
    # Construct request body
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": enable_stream
    }
    
    # Enable web search if requested
    if enable_search:
        # Enable web search functionality for real-time information queries
        # This allows the model to search the internet for current information
        data["enable_search"] = True
    
    # Enable deep thinking mode if requested
    if enable_thinking:
        # Enable deep thinking mode for more thoughtful responses
        # This allows the model to show its reasoning process
        data["enable_thinking"] = True
    
    try:
        if enable_stream:
            # Handle stream response
            response = requests.post(API_URL, headers=headers, json=data, stream=True)
            
            if response.status_code == 200:
                full_reply = ""
                # Process stream response line by line
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        
                        # Skip empty lines and SSE event type lines
                        if not line_str.strip() or line_str.startswith(':'):
                            continue
                        
                        # Skip SSE format prefix
                        if line_str.startswith('data: '):
                            line_str = line_str[6:]
                        
                        # Check for end of stream
                        if line_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(line_str)
                            # Extract content from delta
                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    # Print content immediately (stream output)
                                    print(content, end="", flush=True)
                                    full_reply += content
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                
                print()  # New line after stream ends
                return full_reply
            else:
                error_msg = f"Request failed, status code: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", error info: {error_detail}"
                except:
                    error_msg += f", response content: {response.text}"
                return error_msg
        else:
            # Handle non-stream response
            response = requests.post(API_URL, headers=headers, json=data)
            
            # Check response status code
            if response.status_code == 200:
                # Parse response content
                response_data = response.json()
                # Extract reply content
                reply = response_data.get("choices", [{}])[0].get("message", {}).get("content", "Unable to get reply.")
                return reply
            else:
                error_msg = f"Request failed, status code: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", error info: {error_detail}"
                except:
                    error_msg += f", response content: {response.text}"
                return error_msg
    
    except requests.exceptions.RequestException as e:
        return f"Network request exception: {str(e)}"
    except Exception as e:
        return f"Error occurred: {str(e)}"


def interactive_chat():
    """
    Interactive conversation mode with web search, stream output and deep thinking support
    """
    print("=" * 50)
    print("Qwen Model Conversation System")
    print(f"Web Search: {'Enabled' if ENABLE_WEB_SEARCH else 'Disabled'}")
    print(f"Stream Output: {'Enabled' if ENABLE_STREAM else 'Disabled'}")
    print(f"Deep Thinking: {'Enabled' if ENABLE_DEEP_THINKING else 'Disabled'}")
    print("Type 'Q' or 'quit' to exit conversation")
    print("=" * 50)
    
    conversation_history = []
    
    while True:
        # Prompt user for input
        user_input = input("\nPlease enter your question: ").strip()
        
        # Check if exit
        if user_input.upper() in ['Q', 'QUIT', '退出']:
            print("Conversation ended.")
            break
        
        if not user_input:
            print("Input cannot be empty, please re-enter.")
            continue
        
        # Call function to get reply
        print("\nQwen Reply: ", end="")
        reply = ask_question(
            user_input, 
            conversation_history, 
            enable_search=ENABLE_WEB_SEARCH,
            enable_stream=ENABLE_STREAM,
            enable_thinking=ENABLE_DEEP_THINKING
        )
        
        # For non-stream mode, reply is already printed, but we need to handle it
        if not ENABLE_STREAM and reply:
            print(reply)
        
        # Update conversation history (optional: save conversation context)
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        conversation_history.append({
            "role": "assistant",
            "content": reply if reply else ""
        })
        
        # Limit conversation history length to avoid exceeding token limit
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]


if __name__ == "__main__":
    # Run interactive conversation
    interactive_chat()
