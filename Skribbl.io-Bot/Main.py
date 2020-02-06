# Store dictionary with words and images (Color and black and white?)
# Make game start automatically with 2 bots, I.E. get invite link, paste into other bot
# Fix drawing function

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from time import sleep, time
import cv2
from sys import exit


# Broken!
word_txt = open("word_list.txt", "r+")
g_words_txt = open("guessing_words.txt", "r+")
guess_words = [line.rstrip('\n') for line in g_words_txt.readlines()]
g_words_dict = {k: v for (k, v) in zip(guess_words, [len(word) for word in guess_words])}
lst_words = [line.rstrip('\n') for line in word_txt.readlines()]
words_dict = {k: v for (k, v) in
              zip([item.split(",")[0] for item in lst_words], [item.split(",")[1] for item in lst_words])}

first_run = True
keys_lst = []
guessed_keys = []

# Method to save words to txt file at end of session
def save_words():
    word_txt.close()
    g_words_txt.close()
    print("Words saved.")


def convert_image_b_and_w(keyword):
    image = cv2.imread('C:/Users/Truman/PycharmProjects/SkriblDrawer/images/temp/' + keyword + '.png')
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (thresh, b_and_w_image) = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    print("Converted to B&W")
    # Resize to size of fullscreen canvas on skribbl
    b_and_w_image = cv2.resize(b_and_w_image, (round(814/2), round(611/2)))
    cv2.imwrite('C:/Users/Truman/PycharmProjects/SkriblDrawer/images/' + keyword + "BAW.png",
                b_and_w_image)
    print("Black and white image created")


# Method to add words to main word list
def add_words(word):
    if word not in words_dict:
        lst_words.append(word)
        word_txt.write(word + ",'C:/Users/Truman/PycharmProjects/SkriblDrawer/images/temp/{0}BAW.png'\n".format(word))
    else:
        print("Word already in dictionary")
    if word not in guess_words:
        guess_words.append(word)
        g_words_txt.write(word + "\n")
    else:
        print("Word already in guessing words")


class SkribblBot:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

    def mute_site(self):
        mute_btn = self.driver.find_element_by_xpath('//*[@id="audio"]')
        mute_btn.click()

    def start_game(self):
        name_input = self.driver.find_element_by_xpath('//*[@id="inputName"]')
        name_input.send_keys("Truman")
        play_btn = self.driver.find_element_by_xpath('//*[@id="buttonLoginCreatePrivate"]')
        play_btn.click()

    def find_word(self):
        word_id = self.driver.find_element_by_xpath('//*[@id="currentWord"]')
        word = word_id.text
        add_words(word)

    def google_image_extractor(self, keyword):
        self.driver.execute_script("window.open('')")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get('https://www.google.com.sg/search?q=' + keyword +
                        '&espv=2&biw=1920&bih=989&site=webhp&source=lnms&'
                        'tbm=isch&sa=X&ei=ApZZVdrQJcqWuATcz4K4Cw&sqi=2&ved=0CAcQ_AUoAg')
        image_located = False
        i = 0
        first_result = ""
        while not image_located:
            try:
                first_result = self.driver.find_element_by_class_name("mJxzWe").find_element_by_tag_name('img')\
                    .find_element_by_xpath('//*[@id="islrg"]/div[1]/div[1]/a[1]')
                print("Found first image", first_result)
                image_located = True
            except NoSuchElementException:
                print("Trying again...")
                try:
                    first_result = self.driver.find_element_by_id("main").find_element_by_xpath(
                        '//*[@id="rg_s"]/div[1]/a[1]')
                    print("Found first image", first_result)
                    image_located = True
                except NoSuchElementException:
                    print("No image located.")
                    i += 1
                    if i >= 5:
                        exit()

        # Find href page and navigate to it

        # ONLY WORKS SOMETIMES #

        print("Attempting to find href")
        sleep(1)
        href_located = False
        i = 0
        while not href_located:
            try:
                self.driver.get(first_result.get_attribute("href"))
                print("Found href")
                href_located = True
            except InvalidArgumentException:
                print("No href found, will attempt {0} more times".format(str(4-i)))
                i += 1
                sleep(2)
                if i >= 5:
                    print("Replace with exit")
                    break

        sleep(3)
        # On 'href' page, find source page
        image_src = self.driver.find_element_by_xpath('//*[@id="irc_cc"]/div/div[2]/div[1]/div[2]/div[1]/a/div/img')\
            .get_attribute('src')
        print("Found source image", image_src)
        # Navigate to source page
        self.driver.get(image_src)
        print("Navigated to source page")
        # Take image on source page and screenshot
        final_image = self.driver.find_element_by_tag_name('img')
        print("Found image")
        final_image.screenshot('images/temp/' + keyword + '.png')
        print("Screenshot taken")
        # Close window and go back to main window
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        # Send screenshot to be converted to black and white
        convert_image_b_and_w(keyword)

    def set_brush_size(self):
        small_btn = self.driver.find_element_by_xpath('//*[@id="containerBoard"]/div[2]/div[4]/div[1]')
        small_btn.click()

    def draw(self, keyword):
        image = cv2.imread(words_dict[keyword])
        actions = ActionChains(self.driver)
        canvas = self.driver.find_element_by_xpath('//*[@id="canvasGame"]')
        actions.move_to_element_with_offset(canvas, 0, 0)

        # Drawing

        # Currently way too slow
        # Improve by creating drawing paths per row and then move mouse from beginning of drawing path to end
        # Where drawing paths are lines in rows

        # Speed even more by making the drawing skip every other line, then come back to them

        size_x = image[0]
        row = -1
        movement_lst = []
        for i in image:
            row += 1
            lst_black_points = []
            for j in range(len(size_x)):
                # print("checking " + str(j))
                if 255 not in i[j]:
                    lst_black_points.append(j)
                elif len(lst_black_points) == 0:
                    continue
                else:
                    movement_lst.append((row, lst_black_points[0], lst_black_points[-1]))
                    lst_black_points = []
        print(movement_lst)

        for item in movement_lst:

            def draw_lines():
                t1 = time()
                actions.move_to_element_with_offset(canvas, item[1], item[0])
                actions.click_and_hold()
                actions.move_by_offset(item[2] - item[1], 0)
                actions.release()
                actions.perform()
                actions.reset_actions()
                t2 = time()
                print("Time: " + str(t2 - t1))

            if item[0] % 10 == 0:
                draw_lines()

            if item[0] % 10 - 5 == 0:
                draw_lines()

    def guess(self):
        global keys_lst
        global guessed_keys

        def find_word():
            word_id = self.driver.find_element_by_xpath('//*[@id="currentWord"]')
            length = len(word_id.text)

            return length, word_id.text

        def gen_keys_lst():

            # Add somewhere, if word has a space in it, only generate words with spaces, and vice versa

            global first_run
            length, word_id = find_word()
            global keys_lst
            global guessed_keys
            if first_run:
                keys_lst = [key for (key, value) in g_words_dict.items() if value == length]
                first_run = False
            print(keys_lst)

            if any(c.isalpha() for c in word_id):
                letter = int
                temp_keys_lst = []
                temp_word = list(word_id)
                for i in range(len(temp_word)):
                    if temp_word[i].isalpha():
                        letter = i
                for item in keys_lst:
                    if list(item)[letter] == temp_word[letter]:
                        temp_keys_lst.append(item)
                # keys_lst = temp_keys_lst
                keys_lst = [x for x in temp_keys_lst if x not in guessed_keys]

        # Stop guesses after 4 attempts and wait 2 seconds, then continue guessing

        def start_guessing():
            text_chat = self.driver.find_element_by_id("inputChat")
            global guessed_keys
            i = 0

            t1 = time()
            for item in keys_lst:
                keys_lst.remove(item)
                guessed_keys.append(item)
                t2 = time()
                text_chat.send_keys(item + Keys.ENTER)
                text_chat.send_keys(Keys.ENTER)
                i += 1
                if t2 - t1 > 10 or i >= 4:
                    print("Getting new word list")
                    gen_keys_lst()
                    break

        # Run initial gen_keys
        gen_keys_lst()

        # Move into loop of guessing and pausing as to not get kicked
        while True:
            start_guessing()
            print("Pausing")
            sleep(2)

    def end_session(self):
        self.driver.quit()
        save_words()
        print("Session ending.")
        exit()


# Bot 1

bot = SkribblBot()

bot.driver.get('https://skribbl.io/')
sleep(.5)
bot.mute_site()
bot.start_game()

# bot.google_image_extractor('keyboard')

# Bot 2
# bot2 = SkribblBot()
