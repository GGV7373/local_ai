import ollama

class LlamaBackend:
    def __init__(self, model_name="llama2"):
        self.model_name = model_name

    def generate_response(self, prompt):
        print("Generating response for prompt:", prompt)
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I couldn't process your request."

if __name__ == "__main__":
    llm_backend = LlamaBackend(model_name="llama2")
    user_prompt = "What is the capital of Norway?"
    response = llm_backend.generate_response(user_prompt)
    print("Response:", response)