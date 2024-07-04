# invoke-civitai

## Summary
Convert metadata from InvokeAI for automatic recognition when uploading to CivitAI

## Background
I love InvokeAI much more than Automatic1111 WebUI, because the interface is much more streamlined, user-friendly and it "just works".  
But unfortunately Civitai doesn't recognize metadata from images generated with InvokeAI, so I've written a script to convert InvokeAI metadata format to Automatic1111 format so that Civitai can recognize them.

## How to Use
### Prerequisites
* Python (ideally v3.10 and above)
* InvokeAI (of course)

### Prerequisite Setup for InvokeAI
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

I've used the latter, since the former option has a hard dependency that the models used to generate the images still exist on the user's computer. I might add an option to do that in future, but for now I feel that changing InvokeAI's hashing setting is a more streamlined approach as the hashes can be read directly from the generated images.

### Usage Instructions
1. Drag & Drop the images you want to convert to the `converter.bat` file
2. That's it! The converted images will be saved in the same folder as the original, with `_a1111` appended to the file name

Now you can upload the converted images to Civitai, and all parameters and models (including LoRAs) used by the image will automagically be filled in by Civitai upon upload.
