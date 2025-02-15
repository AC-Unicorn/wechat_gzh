
import os
from pydub import AudioSegment
from openai import OpenAI
client = OpenAI()


def convert_amr_to_mp3(input_amr, output_mp3=None):
    """
    Converts an AMR file to MP3 format.
    
    :param input_amr: Path to the input .amr file.
    :param output_mp3: Path to the output .mp3 file (optional).
    :return: Path to the converted MP3 file.
    """
    if not output_mp3:
        output_mp3 = os.path.splitext(input_amr)[0] + ".mp3"  # Change extension to .mp3

    try:
        # Load the AMR file
        audio = AudioSegment.from_file(input_amr, format="amr")
        
        # Export as MP3
        audio.export(output_mp3, format="mp3")
        
        print(f"Conversion successful: {output_mp3}")
        return output_mp3
    except Exception as e:
        print(f"Error converting {input_amr} to MP3: {e}")
        return None


def audio_to_text(audio_file):
    mp3_path = convert_amr_to_mp3(audio_file)
    file = open(mp3_path, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=file
    )
    return transcription.text