# invoke-civitai

## Summary
Convert metadata from [InvokeAI](https://github.com/invoke-ai/InvokeAI) for automatic recognition when uploading to [CivitAI](https://civitai.com)

## Background
I actually love [InvokeAI](https://github.com/invoke-ai/InvokeAI) more than [Automatic1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui), because the interface is much more streamlined, user-friendly and it "just works".  
But unfortunately Civitai doesn't recognize metadata from images generated with InvokeAI, so I've written a script to convert InvokeAI metadata format to Automatic1111 format so that Civitai can recognize them.

## How to Use
### Prerequisites
* Python (ideally v3.10 and above)
* InvokeAI (of course)

### Option 1: Setup InvokeAI to calculate model hashes in sha256
1. Go to the folder where InvokeAI is installed
2. Open the file `invokeai.yaml` in a text editor
3. Add the line `hashing_algorithm: 'sha256'` so the `invokeai.yaml` file will look something like below:
```yaml
# Internal metadata - do not edit:
schema_version: 4.0.1

# Put user settings here - see https://invoke-ai.github.io/InvokeAI/features/CONFIGURATION/:
hashing_algorithm: 'sha256'
```
4. **!! IMPORTANT !!** Remove all installed models (including LoRAs and VAEs if any), and install them again

InvokeAI by default saves model hashes using `BLAKE3` algorithm, while Automatic1111 saves them using `sha256`. As these hashing algorithms are designed to be unidirectional, it's practically impossible to reverse-engineer a `BLAKE3` back to the original form and convert it to a `sha256` hash.  
But Civitai only understands models identified using a `sha256` hash, so there are two ways around it:  
1. Read in all models used by a particular image, and calculate the `sha256` hash for them
2. Change InvokeAI settings so that `sha256` hashes are saved as metadata in generated images

### Option 2: Setup config file to point to model folders
1. Open `invokeai_cfg.json` in a text editor
2. Change the values of `model_folder`, `vae_folder` and `lora_folder` to the actual locations on your PC where these model files are stored
**!! IMPORTANT !!** Change any backslashes (`\`) to forward slashes (`/`) when entering the model paths

For example, let's say your checkpoint models are stored in `C:\sd\stable-diffusion-webui\models\Stable-Diffusion`, VAE models in `C:\sd\stable-diffusion-webui\models\VAE` and LoRA models in `C:\sd\stable-diffusion-webui\models\Lora`.  
Then change the `invokeai_cfg.json` file like so:
```json
{
    "model_folder": "C:/sd/stable-diffusion-webui/models/Stable-Diffusion",
    "vae_folder": "C:/sd/stable-diffusion-webui/models/VAE",
    "lora_folder": "C:/sd/stable-diffusion-webui/models/Lora"
}
```

### Usage Instructions
1. Download the latest release, and unzip to a new folder
2. Drag & Drop the images you want to convert to the `converter.bat` file
3. That's it! The converted images will be saved in the same folder as the original, with `_a1111` appended to the file name

Now you can upload the converted images to Civitai, and all parameters and models (including LoRAs) used by the image will automagically be filled in by Civitai upon upload.
