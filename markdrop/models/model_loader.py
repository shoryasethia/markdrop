import os

import torch

from ..config_paths import get_gemini_api_key
from ..setup_keys import setup_keys
from .logger import get_logger

logger = get_logger(__name__)

# Cache for loaded models
_model_cache = {}


def detect_device():
    """
    Detects the best available device (CUDA, MPS, or CPU).
    """
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def load_model(model_choice):
    """
    Loads and caches the specified model.
    """
    global _model_cache

    if model_choice in _model_cache:
        logger.info(f"Model '{model_choice}' loaded from cache.")
        return _model_cache[model_choice]

    if model_choice == "qwen":
        device = detect_device()
        logger.info(f"device: {device}.")

        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

        model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-7B-Instruct",
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            device_map="auto",
        )
        print("Qwen2-VL-7B-Instruct has been loaded")
        processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
        device2 = next(model.parameters()).device
        print(f"Model is on device: {device2}")
        # model.to(device)
        _model_cache[model_choice] = (model, processor, device)
        logger.info("Qwen model loaded and cached.")
        return _model_cache[model_choice]

    elif model_choice == "openai":
        from dotenv import load_dotenv

        load_dotenv()

        # Setup OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            setup_keys(provider="openai")

        return api_key, None

    elif model_choice == "gemini":
        from dotenv import load_dotenv

        load_dotenv()

        # Load Gemini model
        import google.generativeai as genai

        api_key = get_gemini_api_key()
        if not api_key:
            setup_keys(provider="gemini")
            api_key = get_gemini_api_key()

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) not found – run: markdrop setup gemini"
            )

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.1-flash-lite")
        return model, None

    elif model_choice == "llama-vision":
        # Load Llama-Vision model
        device = detect_device()

        from transformers import MllamaForConditionalGeneration

        # model_id = "meta-llama/Llama-3.2-11B-Vision-Instruct"
        model_id = "alpindale/Llama-3.2-11B-Vision-Instruct"

        model = MllamaForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            device_map="auto",
        )
        from transformers import AutoProcessor

        processor = AutoProcessor.from_pretrained(model_id)
        model.to(device)
        _model_cache[model_choice] = (model, processor, device)
        logger.info("Llama-Vision model loaded and cached.")
        return _model_cache[model_choice]

    elif model_choice == "pixtral":
        device = detect_device()

        from vllm import LLM  # type: ignore
        from vllm.sampling_params import SamplingParams  # type: ignore

        model = LLM(
            model="mistralai/Pixtral-12B-2409",
            tokenizer_mode="mistral",
            gpu_memory_utilization=0.8,
            max_model_len=8192,
            dtype="float16",
            trust_remote_code=True,
        )
        sampling_params = SamplingParams(max_tokens=1024)
        _model_cache[model_choice] = (model, sampling_params, device)
        return _model_cache[model_choice]

    elif model_choice == "molmo":
        device = detect_device()

        from transformers import AutoModelForCausalLM, AutoProcessor

        processor = AutoProcessor.from_pretrained(
            "allenai/MolmoE-1B-0924", trust_remote_code=True, torch_dtype="auto", device_map="auto"
        )
        model = AutoModelForCausalLM.from_pretrained(
            "allenai/MolmoE-1B-0924", trust_remote_code=True, torch_dtype="auto", device_map="auto"
        )
        _model_cache[model_choice] = (model, processor, device)
        return _model_cache[model_choice]
    else:
        logger.error(f"Invalid model choice: {model_choice}")
        raise ValueError("Invalid model choice.")
