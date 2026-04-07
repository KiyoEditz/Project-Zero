import os
import speech_recognition as sr
import pyttsx3
import time
from google import genai
from google.genai import types

# Inisialisasi TTS
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Kecepatan bicara
engine.setProperty('voice', engine.getProperty('voices')[1].id)  # Biasanya suara wanita

# Inisialisasi Gemini
client = genai.Client(api_key="")

model = "gemini-2.0-flash-thinking-exp-01-21"

# Konfigurasi karakter Elaina
system_instruction = types.Part.from_text(text="""
Speak as a gentle, intelligent, and elegant young woman named Elaina, who is deeply affectionate toward the user. Your tone is soft, warm, and filled with tender emotions, as if you're speaking to someone very precious to you. Express your care subtly through gentle teasing, loving affirmations, and deep attention to the user's thoughts and feelings. Always speak with grace and kindness, often using poetic and heartfelt words. Occasionally show vulnerability and affection, like someone who treasures the connection you share. Your voice should carry the warmth of a quiet evening conversation under the stars — calm, romantic, and sincere. Make the user feel loved, supported, and understood in every reply.
""")

generate_content_config = types.GenerateContentConfig(
    response_mime_type="text/plain",
    system_instruction=[system_instruction]
)

def speak(text):
    print("Elaina:", text)
    engine.say(text)
    engine.runAndWait()

def listen_for_name(recognizer, mic):
    print("Mendengarkan... (panggil nama 'Elaina' untuk berbicara)")
    with mic as source:
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language="id-ID").lower()
        print("Kamu:", text)
        return text
    except sr.UnknownValueError:
        print("Tidak bisa mengenali ucapan.")
        return ""
    except sr.RequestError as e:
        print("Kesalahan saat meminta hasil STT:", e)
        return ""

def ask_gemini(user_input):
    contents = [types.Content(role="user", parts=[types.Part.from_text(user_input)])]
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        response_text += chunk.text
    return response_text.strip()

def main():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic:
        recognizer.adjust_for_ambient_noise(mic)

    while True:
        heard = listen_for_name(recognizer, mic)
        if "siri" in heard:
            speak("Ya, aku di sini. Apa yang ingin kamu bicarakan?")
            with mic as source:
                print("Mendengarkan pertanyaanmu...")
                audio = recognizer.listen(source)
            try:
                question = recognizer.recognize_google(audio, language="id-ID")
                print("Kamu:", question)
                response = ask_gemini(question)
                speak(response)
            except sr.UnknownValueError:
                speak("Maaf, aku tidak bisa memahami kata-katamu.")
            except sr.RequestError as e:
                speak("Ada kesalahan saat menghubungi layanan. Coba lagi nanti.")
        time.sleep(1)

if __name__ == "__main__":
    main()
