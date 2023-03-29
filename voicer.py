import gtts
from playsound import playsound
from argostranslate import package, translate
import argostranslate


text = "" \
       "Internal bleeding"
from_code = 'en'
to_code = 'ru'

package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
print(available_packages)
available_package = list(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    )
)[0]

download_path = available_package.download()

argostranslate.package.install_from_path(download_path)

installed_languages = translate.get_installed_languages()
print(installed_languages)
[str(lang) for lang in installed_languages]
translation_en_ru = installed_languages[0].get_translation(installed_languages[1])
text = translation_en_ru.translate(text)

t1 = gtts.gTTS(text, lang='ru')

t1.save("speech.mp3")

playsound("speech.mp3")
