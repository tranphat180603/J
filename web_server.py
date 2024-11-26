import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.request
from bs4 import BeautifulSoup
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class ContentAnalyzer:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"Self model: {self.model}")

    def fetch_web_content(self, url: str) -> str:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')

                for element in soup(['script', 'style', 'nav', 'footer']):
                    element.decompose()

                text = ' '.join(soup.stripped_strings)
                return text[:8000]
        except Exception as e:
            return f"Error fetching content: {str(e)}"

    def _create_prompt(self, content):
        prompts = {
            'link': lambda c: (
                f"Provide a concise summary and key insights of the following web content:\n"
                f"Source: {c['href']}\n"
                f"Content: {self.fetch_web_content(c['href'])}\n"
                f"Focus on:\n- Main topic\n- Key points\n- Potential value or interesting aspects."
            ),
            'text': lambda c: (
                f"Analyze the following text:\n"
                f"Source: {c.get('source', 'Unknown')}\n"
                f"Text: {c['content']}\n"
                f"Provide:\n- Context\n- Main ideas\n- Potential significance."
            ),
            'image': lambda c: (
                f"Describe the context of this image:\n"
                f"Source: {c['src']}\n"
                f"Alt Text: {c.get('alt', 'No alt text provided')}\n"
                f"Provide:\n- Possible content description\n- Potential context\n- Notable details."
            )
        }
        
        return prompts.get(content['type'], lambda _: None)(content)

    def analyze_content(self, content):
        try:
            prompt = self._create_prompt(content)
            if not prompt:
                return "Invalid content type or missing required fields."

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

        except Exception as e:
            return f"Analysis error: {str(e)}"

# Flask app setup
app = Flask(__name__)
CORS(app)

# Initialize analyzer with the model
analyzer = ContentAnalyzer("Qwen/Qwen2.5-1.5B-Instruct")

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    try:
        content = request.json
        if not content or 'type' not in content:
            return jsonify({"error": "Invalid input. Must include 'type'."}), 400

        analysis = analyzer.analyze_content(content)
        return jsonify({"analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
