# Pallaidium Module Checker
Add-on to check if the gen AI models are running error-free. Needs Pallaidium installed. 

## Download
https://github.com/tin2tin/pallaidium_module_checker/archive/refs/heads/main.zip

## Location 
In the Text Editor side-bar:

![image](https://github.com/user-attachments/assets/7dec5ead-c6d0-4846-a1ef-03c3ee47ecd0)

## Report
A report is written in the Text Editor:
| Model | Status | Notes |
|---|---|---|
| Flux 1 Dev | ✅ | Works as expected. |
| Flux Schnell | ✅ | Works as expected. |
| Flux.1 Kontext Dev | ✅ | Works as expected. |

## How to Uninstall Modules
Hugging Face Diffusers models are downloaded from the hub and saved to a local cache directory. Delete the folder manually:

On Linux and macOS: ~/.cache/huggingface/hub

On Windows: %userprofile%\.cache\huggingface\hub
