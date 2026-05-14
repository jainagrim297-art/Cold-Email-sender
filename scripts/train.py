import sys
sys.stdout.reconfigure(encoding='utf-8')

import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("🚀 Step 1: Loading Dataset...")
# We load the jsonl file you just created
dataset_path = os.path.join(ROOT_DIR, "dataset.jsonl")
dataset = load_dataset("json", data_files=dataset_path, split="train")

print("🧠 Step 2: Preparing the Model for 8GB VRAM...")
# To fit this on your RTX 4060, we shrink the model down to 4-bit math (Quantization)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

# We use TinyLlama because it is small and fast for learning
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token # Required for training

print("🔗 Step 3: Attaching the LoRA Adapter...")
# THIS is the magic. We freeze TinyLlama's brain, and attach a tiny, trainable "adapter" to it.
peft_config = LoraConfig(
    r=8, # The "size" of the adapter. 8 is small and fast.
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"], # We attach the adapter to the AI's Attention mechanism
    bias="none",
    task_type="CAUSAL_LM"
)
# We don't call get_peft_model manually here anymore, SFTTrainer does it automatically!

print("⚙️ Step 4: Configuring the Training Loop...")
# These are the hyperparameters. They control how fast the AI learns.
training_args = SFTConfig(
    output_dir=os.path.join(ROOT_DIR, "custom-b2b-model"),
    per_device_train_batch_size=1, # Keep this at 1 for 8GB VRAM
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=1, # Print updates every step so you can watch it learn
    max_steps=15,    # We only run 15 steps for this quick practice run
    optim="paged_adamw_8bit", # Saves memory
    dataset_text_field="text",
    max_length=128, # Our sentences are short, so we keep this small
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    args=training_args,
)

print("🔥 Step 5: STARTING TRAINING ON RTX 4060! 🔥")
trainer.train()

print("💾 Step 6: Saving your customized AI...")
# This saves the tiny adapter to your hard drive, NOT the whole 4GB model.
adapter_path = os.path.join(ROOT_DIR, "my-b2b-adapter")
trainer.model.save_pretrained(adapter_path)
print(f"✅ Training Complete! Adapter saved to {adapter_path}")