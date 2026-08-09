import asyncio
import base64
import os

import torch
from openai import OpenAI
from PIL import Image
from transformers import GenerationConfig

from .logger import get_logger
from .model_loader import load_model

logger = get_logger(__name__)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_model_device(model):
    """Get the device where the model currently resides"""
    try:
        return next(model.parameters()).device
    except Exception:
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


async def generate_response(
    images, query, resized_height=280, resized_width=280, model_choice="qwen"
):
    """
    Generates a response using the selected model based on the query and images asynchronously.
    """
    try:
        logger.info(f"Generating response using model '{model_choice}'.")

        if model_choice == "qwen":
            from qwen_vl_utils import process_vision_info  # type: ignore

            model, processor, _ = load_model("qwen")
            device = get_model_device(model)
            print(f"Qwen Model loaded on device: {device}")

            resized_height = (resized_height // 28) * 28
            resized_width = (resized_width // 28) * 28

            image_contents = []
            for image in images:
                image_contents.append(
                    {
                        "type": "image",
                        "image": image,
                        "resized_height": resized_height,
                        "resized_width": resized_width,
                    }
                )
            messages = [
                {
                    "role": "user",
                    "content": image_contents + [{"type": "text", "text": query}],
                }
            ]
            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )

            # Move inputs to model's device
            inputs = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()
            }

            # Wrap synchronous HF model generation in to_thread
            def _run_qwen():
                generated_ids = model.generate(**inputs, max_new_tokens=1024)
                generated_ids_trimmed = [
                    out_ids[len(in_ids) :]
                    for in_ids, out_ids in zip(inputs.input_ids, generated_ids, strict=True)
                ]
                return processor.batch_decode(
                    generated_ids_trimmed,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )

            output_text = await asyncio.to_thread(_run_qwen)
            logger.info("Response generated using Qwen model.")
            return output_text[0]

        elif model_choice == "gemini":
            # Load Gemini model
            from google import genai

            from ..config_paths import get_gemini_api_key

            api_key = get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY (or GOOGLE_API_KEY) not found – run: markdrop setup gemini"
                )

            client = genai.Client(api_key=api_key)

            try:
                content = []
                content.append(query)

                for img_path in images:
                    if os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            content.append(img)
                        except Exception as e:
                            logger.error(f"Error opening image {img_path}: {e}")
                    else:
                        logger.warning(f"Image file not found: {img_path}")

                if len(content) == 1:
                    return "No images could be loaded for analysis."

                def _run_gemini():
                    return client.models.generate_content(
                        model="gemini-3.1-flash-lite", contents=content
                    )

                response = await asyncio.to_thread(_run_gemini)

                if response.text:
                    generated_text = response.text
                    import re

                    generated_text = re.sub(r"\*\*(.*?)\*\*", r"\1", response.text)
                    generated_text = re.sub(r"\*(.*?)\*", r"\1", generated_text)
                    generated_text = re.sub(r"\`(.*?)\`", r"\1", generated_text)
                    generated_text = re.sub(r"\[.*?\]\(.*?\)", "", generated_text)
                    generated_text = re.sub(r"\!\[.*?\]\(.*?\)", "", generated_text)
                    logger.info("Response generated using Gemini model.")
                    return generated_text
                else:
                    return "The Gemini model did not generate any text response."

            except Exception as e:
                logger.error(f"Error in Gemini processing: {str(e)}", exc_info=True)
                return f"An error occurred while processing the images: {str(e)}"

        elif model_choice == "openai":
            api_key = load_model(model_choice)
            client = OpenAI(api_key=api_key)
            content = [{"type": "text", "text": query}]

            for img_path in images:
                with open(img_path, "rb") as img_file:
                    base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        }
                    )

            try:

                def _run_openai():
                    return client.chat.completions.create(
                        model="gpt-5.6-terra",
                        messages=[{"role": "user", "content": content}],
                        max_tokens=300,
                    )

                response = await asyncio.to_thread(_run_openai)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return f"Error: {str(e)}"

        elif model_choice == "llama-vision":
            model, processor, _ = load_model("llama-vision")
            device = get_model_device(model)
            print(f"LLaMA-Vision Model loaded on device: {device}")

            image_path = images[0]
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            image = Image.open(image_path).convert("RGB")

            messages = [
                {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": query}]}
            ]
            input_text = processor.apply_chat_template(messages, add_generation_prompt=True)

            # Move inputs to model's device
            inputs = processor(image, input_text, return_tensors="pt")
            inputs = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()
            }

            def _run_llama():
                output = model.generate(**inputs, max_new_tokens=512)
                return processor.decode(output[0], skip_special_tokens=True)

            response = await asyncio.to_thread(_run_llama)
            return response

        elif model_choice == "pixtral":
            try:
                model, sampling_params, _ = load_model("pixtral")
                device = get_model_device(model)
                print(f"Pixtral Model loaded on device: {device}")

                def image_to_data_url(image_path):
                    with open(image_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    ext = os.path.splitext(image_path)[1][1:]
                    return f"data:image/{ext};base64,{encoded_string}"

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": query},
                            *[
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_to_data_url(img_path)},
                                }
                                for i, img_path in enumerate(images)
                                if i < 1
                            ],
                        ],
                    },
                ]

                def _run_pixtral():
                    return model.chat(messages, sampling_params=sampling_params)

                outputs = await asyncio.to_thread(_run_pixtral)
                return outputs[0].outputs[0].text

            except Exception as e:
                raise ValueError("An error occurred while processing the request.") from e

        elif model_choice == "molmo":
            model, processor, _ = load_model("molmo")
            device = get_model_device(model)
            print(f"Molmo Model loaded on device: {device}")
            model = model.half()

            pil_images = []
            for img_path in images[:1]:
                if os.path.exists(img_path):
                    try:
                        img = Image.open(img_path).convert("RGB")
                        pil_images.append(img)
                    except Exception as e:
                        logger.error(f"Error opening image {img_path}: {e}")
                else:
                    logger.warning(f"Image file not found: {img_path}")

            if not pil_images:
                return "No images could be loaded for analysis."

            try:
                inputs = processor.process(images=pil_images, text=query)

                # Move inputs to model's device
                inputs = {
                    k: (
                        v.to(device).unsqueeze(0).half()
                        if v.dtype in [torch.float32, torch.float64]
                        else v.to(device).unsqueeze(0)
                    )
                    if isinstance(v, torch.Tensor)
                    else v
                    for k, v in inputs.items()
                }

                def _run_molmo():
                    with torch.no_grad():
                        output = model.generate_from_batch(
                            inputs,
                            GenerationConfig(max_new_tokens=200, stop_strings="<|endoftext|>"),
                            tokenizer=processor.tokenizer,
                        )

                    generated_tokens = output[0, inputs["input_ids"].size(1) :]
                    return processor.tokenizer.decode(generated_tokens, skip_special_tokens=True)

                generated_text = await asyncio.to_thread(_run_molmo)

                return generated_text

            except Exception as e:
                logger.error(f"Error in Molmo processing: {str(e)}", exc_info=True)
                return f"An error occurred while processing the images: {str(e)}"
            finally:
                for img in pil_images:
                    img.close()

        else:
            logger.error(f"Invalid model choice: {model_choice}")
            return "Invalid model selected."

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "An error occurred while generating the response."
