import os
import argparse
import json
import hashlib
from   typing import Any
from   PIL import Image
from   PIL.PngImagePlugin import PngInfo

# Define Sampler/Scheduler Information
# Need to be updated whenever new Samplers are added to InvokeAI
sampler_info = {
    'euler': {'name': 'Euler', 'type': 'Automatic'},
    'deis': {'name': 'DEIS', 'type': 'Automatic'},
    'ddim': {'name': 'DDIM', 'type': 'Automatic'},
    'ddpm': {'name': 'DDPM', 'type': 'Automatic'},
    'dpmpp_sde': {'name': 'DPM++ SDE', 'type': 'Automatic'},
    'dpmpp_2s': {'name': 'DPM++ 2S', 'type': 'Automatic'},
    'dpmpp_2m': {'name': 'DPM++ 2M', 'type': 'Automatic'},
    'dpmpp_2m_sde': {'name': 'DPM++ 2M SDE', 'type': 'Automatic'},
    'heun': {'name': 'Heun', 'type': 'Automatic'},
    'kdpm_2': {'name': 'KDPM 2', 'type': 'Automatic'},
    'lms': {'name': 'LMS', 'type': 'Automatic'},
    'pndm': {'name': 'PNDM', 'type': 'Automatic'},
    'unipc': {'name': 'UniPC', 'type': 'Automatic'},
    'euler_k': {'name': 'Euler', 'type': 'Karras'},
    'dpmpp_sde_k': {'name': 'DPM++ SDE', 'type': 'Karras'},
    'dpmpp_2s_k': {'name': 'DPM++ 2S', 'type': 'Karras'},
    'dpmpp_2m_k': {'name': 'DPM++ 2M', 'type': 'Karras'},
    'dpmpp_3m_k' :{'name': 'DPM++ 3M', 'type': 'Karras'},
    'dpmpp_2m_sde_k': {'name': 'DPM++ 2M SDE', 'type': 'Karras'},
    'heun_k': {'name': 'Heun', 'type': 'Karras'},
    'lms_k': {'name': 'LMS Karras', 'type': 'Karras'},
    'euler_a': {'name': 'Euler a', 'type': 'Automatic'},
    'kdpm_2_a': {'name': 'KDPM 2a', 'type': 'Automatic'},
    'lcm': {'name': 'LCM', 'type': 'Automatic'},
    'tcd': {'name': 'TCD', 'type': 'Automatic'}
}

def save_model_hash(basename:str, model_hash:str, hash_cache:Any) -> None:
    # Save calculated model hash to cache so that it can be quickly recalled later
    hash_cache[basename] = model_hash
    with open("./hash_cache.json", "w") as f:
        f.write(json.dumps(hash_cache, indent=4))

# From Automatic1111 source code (./modules/hashes.py)
def calculate_sha256(filename:str) -> str:
    try:
        hash_sha256 = hashlib.sha256()
        blksize = 1024 * 1024
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(blksize), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return "NOFILE"

def calculate_shorthash(filename:str, hash_cache:Any) -> str:
    if os.path.basename(filename) in hash_cache and "NOFILE" != hash_cache[os.path.basename(filename)]:
        shorthash = hash_cache[os.path.basename(filename)]
    else:
        print(f"    Calculating model hash for {os.path.basename(filename)}. This will take a few seconds...", flush=True)
        longhash = calculate_sha256(filename)
        shorthash = longhash[0:10]
        save_model_hash(os.path.basename(filename), shorthash, hash_cache)
    return shorthash

def main() -> None:
    # Initialize configuration
    invokeai_cfg = {}

    # Cache previously calculated hashes so that they can be quickly retrieved
    hash_cache = {}

    parser = argparse.ArgumentParser(description="Convert InvokeAI generated images to Automatic1111 format, for easy upload to Civitai")
    parser.add_argument("filename", type=str, nargs='+', help="PNG file generated by InvokeAI")
    args = parser.parse_args()

    if os.path.exists("./invokeai_cfg.json"):
        with open("./invokeai_cfg.json", "r") as f:
            print("    Config file found", flush=True)
            invokeai_cfg = json.load(f)

    if os.path.exists("./hash_cache.json"):
        with open("./hash_cache.json", "r") as f:
            print("    Hash cache found", flush=True)
            hash_cache = json.load(f)

    file_count = len(args.filename)
    successes  = 0

    for filename in args.filename:
        # Load file and import metadata
        print(f"    Processing file: {filename}", flush=True)
        im_invoke = Image.open(filename)
        im_invoke.load()
        if 'invokeai_metadata' not in im_invoke.info:
            print(f"        ERROR: {filename} is not generated by InvokeAI! Skipping file...")
            continue
        json_data = json.loads(im_invoke.info['invokeai_metadata'])

        # Check for inpainting
        if '_canvas_objects' in json_data:
            print(f"        INFO: This is an in-painted image. Attempting to load metadata from original image")
            if 'invokeai_output_folder' in invokeai_cfg:
                if 'imageName' in json_data['_canvas_objects'][0]:
                    org_filename = json_data['_canvas_objects'][0]['imageName']
                    org_filepath = os.path.join(invokeai_cfg['invokeai_output_folder'], org_filename)
                    if os.path.exists(org_filepath):
                        im_original = Image.open(org_filepath)
                        im_original.load()
                        json_data = json.loads(im_original.info['invokeai_metadata'])
                        del im_original
                    else:
                        print(f"        ERROR: Original image {org_filename} not found! Skipping file...")
                        continue
            else:
                print(f"        ERROR: InvokeAI Output folder not configured in invokeai_cfg.json! Skipping file...")
                continue

        # Build base metadata
        meta_positive = json_data['positive_prompt']
        meta_negative = ''
        if 'negative_prompt' in json_data:
            meta_negative = '\nNegative prompt: ' + json_data['negative_prompt']
        meta_steps = '\nSteps: ' + str(json_data['steps'])
        meta_sampler = ''
        meta_type = ''
        if 'scheduler' in json_data:
            meta_sampler = 'Sampler: ' + sampler_info[json_data['scheduler']]['name']
            meta_type = 'Schedule type: ' + sampler_info[json_data['scheduler']]['type']
        meta_cfg = ''
        if 'cfg_scale' in json_data:
            meta_cfg = 'CFG scale: ' + str(json_data['cfg_scale'])
        meta_seed = 'Seed: ' + str(json_data['seed'])
        meta_size = 'Size: ' + str(json_data['width']) + 'x' + str(json_data['height'])
        meta_mname = 'Model: ' + json_data['model']['name']

        # Build metadata for checkpoint model
        if 'sha256:' in json_data['model']['hash']:
            model_hash = json_data['model']['hash'].replace('sha256:','')[:10]
            meta_mhash = 'Model hash: ' + model_hash
            save_model_hash(f"{json_data['model']['name']}.safetensors", model_hash, hash_cache)
        else:
            print("        Model hash is not sha256! Attempting to calculate hash from model file", flush=True)
            if 'model_folder' in invokeai_cfg:
                model_file = f"{invokeai_cfg['model_folder']}/{json_data['model']['name']}.safetensors"
                model_hash = calculate_shorthash(model_file, hash_cache)
                if model_hash != "NOFILE":
                    meta_mhash = 'Model hash: ' + model_hash
                else:
                    print(f"        ERROR: Model file {model_file} not found! Skipping file...", flush=True)
                    continue
            else:
                print(f"        ERROR: Model folder not configured in invokeai_cfg.json! Skipping model {json_data['model']} ...", flush=True)
                continue
        meta_params = [meta_steps, meta_sampler, meta_type, meta_cfg, meta_seed, meta_size, meta_mhash, meta_mname]

        # Build metadata for VAE model
        if 'vae' in json_data.keys():
            meta_vname = 'VAE: ' + json_data['vae']['name'] + '.safetensors'
            if 'sha256:' in json_data['vae']['hash']:
                model_hash = json_data['vae']['hash'].replace('sha256:','')[:10]
                meta_vhash = 'VAE hash: ' + model_hash
                save_model_hash(f"{json_data['vae']['name']}.safetensors", model_hash, hash_cache)
            else:
                print("        Model hash is not sha256! Attempting to calculate hash from model file", flush=True)
                if 'vae_folder' in invokeai_cfg:
                    model_file=f"{invokeai_cfg['vae_folder']}/{json_data['vae']['name']}.safetensors"
                    model_hash = calculate_shorthash(model_file, hash_cache)
                    if model_hash != "NOFILE":
                        meta_vhash = 'VAE hash: ' + model_hash
                    else:
                        print(f"        ERROR: Model file {model_file} not found! Skipping file...", flush=True)
                        continue
                else:
                    print(f"        ERROR: Model folder not configured in invokeai_cfg.json! Skipping model {meta_vname}...", flush=True)
                    continue
            meta_params.append(meta_vhash)
            meta_params.append(meta_vname)

        # Build metadata for LoRA model
        if 'loras' in json_data.keys():
            meta_lora = 'Lora hashes: "'
            for idx, lora in enumerate(json_data['loras']):
                lora_name = lora['model']['name']
                if 'sha256:' in lora['model']['hash']:
                    model_hash = lora['model']['hash'].replace('sha256:','')[:10]
                    lora_hash = model_hash
                    save_model_hash(f"{lora['model']['name']}.safetensors", model_hash, hash_cache)
                else:
                    print("        Model hash is not sha256! Attempting to calculate hash from model file", flush=True)
                    if 'lora_folder' in invokeai_cfg:
                        model_file=f"{invokeai_cfg['lora_folder']}/{lora['model']['name']}.safetensors"
                        lora_hash = calculate_shorthash(model_file, hash_cache)
                        if lora_hash == "NOFILE":
                            print(f"        ERROR: Model file {model_file} not found! Skipping file...", flush=True)
                            continue
                    else:
                        print(f"        ERROR: Model folder not configured in invokeai_cfg.json! Skipping LORA {lora_name}...", flush=True)
                        continue
                meta_lora += lora_name + ': ' + lora_hash
                meta_positive += ' <lora:' + lora_name + ':' + str(lora['weight']) + '>'
                if idx < len(json_data['loras']) - 1:
                    meta_lora += ', '
            meta_lora += '"'
            meta_params.append(meta_lora)
        meta_version = 'Version: v1.9.4' # Hard-code to imitate Automatic1111
        meta_params.append(meta_version)
        meta_final = meta_positive + meta_negative + ', '.join(meta_params)

        # Create a PngInfo object to hold the metadata
        metadata = PngInfo()
        metadata.add_text("parameters", meta_final)

        # Save the image with the metadata
        new_filename = os.path.join(os.path.dirname(filename), os.path.basename(filename).split('.')[0] + '_a1111.' + os.path.basename(filename).split('.')[1])
        im_invoke.save(new_filename, pnginfo=metadata)
        print(f"    Converted file saved as: {new_filename}", flush=True)
        successes += 1

    print(f"Work complete. {successes} / {file_count} files successfully converted.")

if __name__ == "__main__":
    main()