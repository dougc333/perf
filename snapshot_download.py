from huggingface_hub import snapshot_download

# same repo id (or local path) you passed to from_pretrained
checkpoint_dir = snapshot_download(
    "Qwen/Qwen3-0.6B",
    local_dir="/content/models/Qwen3-0.6B",
  )  
print(checkpoint_dir)