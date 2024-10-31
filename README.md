# Whispering Wizard 🧙‍♂

Welcome to **Whispering Wizard** – the spellbindingly simple transcription tool that turns your audio into text, no magic wand required! 

This is a **zero-hassle** app designed for folks who just want to get their audio transcribed without fiddling around with techy stuff. No FFmpeg installed? No problem! Whispering Wizard doesn’t care about what’s on your system – it **downloads its very own enchanted version** of FFmpeg right into its folder. And if that’s not enough magic for you, it’ll also summon any Whisper model you choose, ensuring you’ve got the power to transcribe your way.

Importantly, all processing of your audio files is done locally on your computer - this application does not use the Whisper API, and your data is not transmitted to the cloud, or anywhere.

## Features ✨

- **Magical FFmpeg Setup**: You don’t need to lift a finger (or type a command) to install FFmpeg. Whispering Wizard downloads its own local copy – no muss, no fuss.
- **Whisper Model Support**: Choose from a range of Whisper models – from the petite `tiny` to the mighty `large` and `turbo` models – depending on how fast or accurate you need your transcriptions to be.
- **Audio Format Wizardry**: Whispering Wizard transcribes audio from various formats, handling `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`, `.webm`, and more. Your files will feel like they’re in a mystical cauldron of compatibility.
- **Video Format Enchantment**: Whispering Wizard can now extract and transcribe audio directly from popular video formats, including `.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, `.wmv`, `.mpeg`, `.3gp`, `.asf`, and more! Just drop in your video files, and let the magic reveal their voices.
- **Timestamp Sorcery**: Want timestamps? Just check a box, and they’ll appear in your transcripts like clockwork.
- **Custom Output Magic**: Get your transcriptions as individual `.txt` files or a single, organized `.csv`. Your text, your way.

## How to Run

To download the latest version of _Whispering Wizard_, just head over to the [releases page](https://github.com/ryanboyd/WhisperingWizard/releases). You can also run/build/modify the program directly from the source code as well 🎃


## How to Use 🧙‍♀️

1. **Pick Your Model**: 
   Select from a range of Whisper models. Want it fast? Go for the smaller models. Need top-notch accuracy? The larger models are here to help. Just like picking the right potion, it’s all about the balance.

2. **Choose Input and Output Folders**:
   - Click **"Select Input Folder"** to choose the folder where your audio files live.
   - Then, **"Select Output Folder"** to decide where the magic (i.e., transcriptions) will be stored.

3. **Decide on Timestamps**: 
   Do you want timestamps sprinkled into your transcriptions? Check the box to add them or leave it unchecked if you want just the raw text.

4. **Pick Your Potion – Output Format**:
   - **Text Files**: One `.txt` file for each audio file.
   - **CSV**: One big `.csv` file with all the audio files neatly transcribed and organized.

5. **Hit the Button and Watch the Magic Happen**:
   - Press the **"Start Transcription"** button and let the wizard work its magic.
   - You’ll see a progress bar – it’s kind of like stirring a potion, but much less messy.

6. **Wait for the Incantation to Finish**:
   Once the transcription is complete, you’ll get a message saying the spell has been successfully cast (a.k.a. your transcription is done). 🎉

## A Little FFmpeg Magic 🧙‍♂️

No need to go on a quest for FFmpeg – Whispering Wizard **doesn’t even look for it** on your system. It will download its very own copy directly to the application folder, ensuring no other spells interfere with your transcription magic. So even if you’ve never heard of FFmpeg (or can’t pronounce it), Whispering Wizard has got you covered.

## FAQ 🧩

- **Q**: What audio formats can Whispering Wizard handle?
  - **A**: Anything from `.mp3`, `.wav`, `.flac`, to `.m4a`, `.ogg`, `.mp4`, `.webm`. If it makes sound, *Whispering Wizard* can probably transcribe it.

- **Q**: Does Whispering Wizard need an internet connection?
  - **A**: Only for the first time, when it downloads its very own copy of FFmpeg and any time you need to download a new Whisper model. After that, you’re good to go offline and transcribe to your heart's content!

- **Q**: Do I need to know anything about FFmpeg or models?
  - **A**: Nope! Whispering Wizard handles all the techy stuff in the background while you sit back and enjoy the magic.

So there you have it – **Whispering Wizard**: no install drama, just pure transcription magic. Get ready to transcribe like a wizard! 🪄

# Important Note 📝

## The True Wizards Behind the Curtain ✨

While **Whispering Wizard** makes it easy to transcribe your audio files with just a few clicks, the real power behind this application comes from some incredible tools built by others:

- **OpenAI's Whisper**: Whispering Wizard uses OpenAI’s powerful Whisper models for transcription. These models are responsible for converting your audio into text with high accuracy. They’re the true magic at work here.

- **FFmpeg**: Handling all the audio decoding, conversion, and processing, FFmpeg is a world-class multimedia framework. Whispering Wizard doesn’t require you to install FFmpeg separately—it automatically downloads its own copy to work with. Kudos — as always — to the unbelievable work that the FFmpeg team puts into maintaining such a versatile and world-class tool!

## What Whispering Wizard *Really* Does 🧙‍♂️

Whispering Wizard is simply a **graphical user interface (GUI)** designed to make these amazing technologies more accessible. It provides a user-friendly way to tap into the power of Whisper and FFmpeg without requiring you to dive into the command line.

In other words, Whispering Wizard is **a wrapper** around these tools, guiding you through the transcription process so you don’t have to worry about the technical details. This application just make it easier for you to leverage the brilliance of the real wizards behind the scenes.

## Shout-Outs 💖

A wizardly thank you to:
- The **OpenAI team** for developing Whisper and making it publicly available.
- The **FFmpeg team** for their hard work in creating and maintaining an indispensable multimedia toolkit.

Without these incredible projects, Whispering Wizard would be nothing more than an empty robe! 🎩✨

