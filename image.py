import os, random, math, time
from queue import Queue
from threading import Thread, Event
from PIL import Image, ImageEnhance
import numpy as np
from config import INPUT_FOLDER, OUTPUT_FOLDER, IMAGE_SIZE, BATCH_SIZE, COLORED


class ImageVariations():
    def __init__(self, image_size=IMAGE_SIZE, batch_size=BATCH_SIZE, in_memory=True, input_folder=INPUT_FOLDER):
        #Parameters
        self.image_size = image_size
        self.input_folder = input_folder
        self.in_memory = in_memory
        self.batch_size = batch_size
        #Variation Config
        self.max_rotation = 30
        self.brightness_range = (0.7, 1.1)
        self.saturation_range = (0.7, 1.)
        self.contrast_range = (0.8, 1.2)
        #Threads
        self.queue = Queue()
        self.files = os.listdir(input_folder)
        num_threads = os.cpu_count()
        if num_threads is None:
            num_threads = 4
        self.threads = [Thread(target=self.thread, args=(self.files[i::num_threads],), daemon=True)
                        for i in range(num_threads)]
        self.event = Event()
        self.closing = False
        for t in self.threads:
            t.start()

    def get_batch(self):
        self.event.set()
        images = [self.queue.get() for i in range(self.batch_size)]
        self.event.clear()
        return images

    def close(self):
        self.closing = True
        self.event.set()

    def thread(self, files):
        if self.in_memory:
            if COLORED:
                images = [Image.open(os.path.join(self.input_folder, file)) for file in files]
            else:
                images = [Image.open(os.path.join(self.input_folder, file)).convert("L") for file in files]
        while True:
            if self.in_memory:
                image = random.choice(images)
            else:
                image = Image.open(os.path.join(self.input_folder, random.choice(files)))
                if not COLORED:
                    image = image.convert("L")
            arr = np.asarray(self.get_variation(image), dtype=np.float)
            if not COLORED:
                arr.shape = arr.shape+(1,)
            self.queue.put(arr)
            if self.closing:
                return
            if self.queue.qsize() >= self.batch_size*3:
                self.event.wait()

    def get_variation(self, image):
        #Crop
        min_dim = min(image.size)
        scale = math.sqrt(2)*self.image_size*1.1
        if scale*3 < min_dim:
            scale = random.uniform(0.3, 0.7)
        elif scale*2 < min_dim:
            scale = random.uniform(min_dim, min_dim - scale)/min_dim
        else:
            scale = random.uniform(scale, min_dim)/min_dim
        size = int(random.random()*min_dim*(1-scale)+min_dim*scale)
        pos = (random.randrange(0, image.size[0]-size), random.randrange(0, image.size[1]-size))
        image = image.crop((pos[0], pos[1], pos[0]+size, pos[1]+size))
        #Rotate
        size = image.size[0]/math.sqrt(2)
        offset = (image.size[0]-size)/2
        rotation = random.randint(-self.max_rotation, self.max_rotation)
        image = image.rotate(rotation).crop((offset, offset, offset+size, offset+size))
        #Transpose
        if random.random() < 0.5:
            image.transpose(Image.FLIP_LEFT_RIGHT)
        #Variation
        brightness = random.uniform(*self.brightness_range)
        if np.abs(brightness-1.0) > 0.05:
            image = ImageEnhance.Brightness(image).enhance(brightness)
        if COLORED:
            saturation = random.uniform(*self.saturation_range)
            if np.abs(saturation-1.0) > 0.05:
                image = ImageEnhance.Color(image).enhance(saturation)
        contrast = random.uniform(*self.contrast_range)
        if np.abs(contrast-1.0) > 0.05:
            image = ImageEnhance.Contrast(image).enhance(contrast)
        return image.resize((self.image_size, self.image_size), Image.LANCZOS)


def save_image(image, size=IMAGE_SIZE, name=None, output_folder=OUTPUT_FOLDER):
    os.makedirs(output_folder, exist_ok=True)
    image.shape = (size, size, 3) if COLORED else (size, size)
    img = Image.fromarray(np.array(image, dtype=np.uint8), ("RGB" if COLORED else "L"))
    add_time = time.time() - 1490000000
    if name is None:
        path = os.path.join(output_folder, "%d_test.png"%add_time)
    else:
        path = os.path.join(output_folder, '%d_%s.png'%(add_time, name))
    img.save(path, 'PNG')


if __name__ == "__main__":
    if len(os.sys.argv) > 1:
        imgvariations = ImageVariations(in_memory=False, batch_size=int(os.sys.argv[1]))
        images_batch = imgvariations.get_batch()
        imgvariations.close()
        for i in range(int(os.sys.argv[1])):
            save_image(images_batch[i], name="variant_%d"%i)
        print("Generated %s image variations as they are when fed to the network"%os.sys.argv[1])
    else:
        print("Testing memory requiremens")
        imgvariations = ImageVariations(batch_size=BATCH_SIZE)
        input("Press Enter to continue... (all images loaded)")
        iml1 = imgvariations.get_batch()
        iml2 = imgvariations.get_batch()
        iml3 = imgvariations.get_batch()
        iml4 = imgvariations.get_batch()
        input("Press Enter to continue... (also four batches)")
