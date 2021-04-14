from captcha.image import ImageCaptcha
import random
import string
image = ImageCaptcha(fonts=['./static/fonts/quicksand.ttf'])


def randomString(size=5, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
captchaText = randomString()
data = image.generate(captchaText)
image.write(captchaText, f'{captchaText}.png')