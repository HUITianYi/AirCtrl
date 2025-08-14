# AirCtrl
AirCtrl is a computer vision-based gesture interaction platform, which captures hand movements through a camera to achieve contactless interface operation. AirCtrl supports a variety of interactive scenarios, including drawing, games, VR simulation, etc., and is committed to providing users with a more intuitive and convenient operation experience.

# Key features🗝️
Multi-modal gesture recognition: support piching🤌, fist clenching✊, five-finger opening🖐️, victory sign✌️, index finger pointing☝️ and other common gestures.

# Enrich interactive scenarios🪄
## 🎨 Van Gogh Canvas: 
  Shake off the hassle of paints and brushes 🚫—create freely in mid-air, anytime, anywhere! Raise your arm bold as Van Gogh , and sketch your very own "Starry Night" 🌌. With a rainbow of brushes 🖍️, squishy erasers 🧽, and fun stickers ✨, painting turns into a breeze—light, lively, and full of giggles 😄!
## 🏏 Gesture-Controlled paddle Ball:
  Guide the ball with a wave of your hand 👋, no clunky controllers required! Dive into a totally new gaming groove—where every flick and swish sparks a rush of playful excitement ⚡!
## 🎮 VR "Pac-Man":
  Whether solo or teaming up 👥, dive into hyper-immersive gesture-controlled fun! With a flick of your wrist, navigate the maze like magic 🕶️—this ain’t just VR, it’s a whole new virtual adventure blast 🚀! Grab your bestie and let the munching mayhem begin 👫!

# Technology stack⚙️

Language: Python

GUI framework: PyQt5

Computer Vision: OpenCV

Gesture tracking: MediaPipe

Gesture logic: Custom gesture recognition algorithm based on joint Angle calculation

## Quick start🕹️
# Prior dependency

Before you start using AirCtrl, make sure you have the following dependencies installed:
```
pip install pyqt5 opencv-python mediapipe
```
Running methods

Clone the repository locally:
```
git clone https://github.com/your-repo-name/AirCtrl.git
```

Go to the project directory:
```
cd AirCtrl
```

Run the main program:
```
python My_Project/main.py
```
## Gesture operation Instructions👋

# Pinch gesture: Used for selection or confirmation.
<img width="424" height="446" alt="0986631bb39042a78ec46cc23ccb3b40" src="https://github.com/user-attachments/assets/f103e887-dc99-43db-8158-8e730731f9d6" />

# Index finger pointing: Controls cursor movement.
<img width="468" height="522" alt="6ce3d10d7703f7ee52ce126aa3daaa4e" src="https://github.com/user-attachments/assets/4a9e4bf8-3824-409c-b6c1-c4e5207a65a8" />

# Five fingers open: To be determined.
<img width="524" height="526" alt="fcf82671205070bf350ef950390c1658" src="https://github.com/user-attachments/assets/bf200b3c-94e7-4e18-b09d-cd7303df964d" />

# Closed Fist: To be determined.
<img width="489" height="508" alt="de6328951338b43b0bb03288956f0db8" src="https://github.com/user-attachments/assets/d57d23bb-9b59-4705-9814-824702572574" />

# Thumb UP: To be determined.
<img width="503" height="512" alt="b7ed93c5f1657dce84bf18c67a3c635b" src="https://github.com/user-attachments/assets/e5002a4d-f662-49e1-8768-c305b53016ff" />


## Interface Preview📲

Here are some screenshots of the core features of the project:

Main menu interface: Shows all available gesture operation modes.
![111](https://github.com/user-attachments/assets/a7b13cce-a63f-4b92-8bad-7c45ab6c0c27)

### 🎨 Van Gogh Canvas——Drawing function demonstration: 
display gesture drawing pad, support real-time drawing.
![Adobe Express - 打开draw](https://github.com/user-attachments/assets/54cb244a-d877-4d7b-944b-b21dd291a18b)
#### 🖌️ Brushes: Pick from a rainbow of colors, swap tip thickness at will—lines flow smooth as clouds, and sketching starry skies? Total breeze～
![Adobe Express - 8月14日 (2)](https://github.com/user-attachments/assets/f81a1668-53ad-4533-ae30-1197d5a20b18)
#### 🧽 Erasers: Swish gently to "munch" away wrong strokes, leaving zero traces—spotless! Tweaking your art? So effortless!
![Adobe Express - 8月14日 (2)(1)](https://github.com/user-attachments/assets/5d8c52f1-f78f-4e96-9c57-beb776b41a27)
#### ✨ Stickers: Browse a cute vault of stickers—flowers, stars, little monsters... Tap to stick 'em, and poof! Tiny surprises bloom in your work～
![贴纸draw](https://github.com/user-attachments/assets/e6c0c516-5a98-4f0a-9a21-04eca02682e9)
#### 👆 Drag: Oops, wrong spot? No sweat! Drag through the air with your fingertip—stickers and lines "obey" and shift. Flexible adjustments, zero hassle!
![Adobe Express - 8月14日 (2)(2)](https://github.com/user-attachments/assets/b2e10a9e-96ed-4eb3-bd4d-c4c0b203958f)
#### 🗑️ Clear canvas: Craving a redo? Flash an "erase" gesture and done! Canvas wipes clean in a blink—start fresh, no stress, all fun～
![Adobe Express - 8月14日 (2)(3)](https://github.com/user-attachments/assets/250cd78c-d3aa-42f0-be15-06722a0a5e1a)



## Game interface: 
### 🏏 Gesture-Controlled paddle Ball——Display gesture control of the baffle ball game scene.
![Adobe Express - Paddle_game](https://github.com/user-attachments/assets/bfe9f229-7391-41fd-9f0b-4620905ba12b)
#### 👉👉 Your fingertip’s just morphed into a paddle! Hustle—don’t let that ball hit the ground ⚽!

### 🎮 VR "Pac-Man"——Whether solo or teaming up 👥, dive into hyper-immersive gesture-controlled fun! With a flick of your wrist, navigate the maze like magic 🕶️
![8月14日 (2)(4)](https://github.com/user-attachments/assets/b481741e-4c83-4dc9-9a8c-1e3a274b85ab)
#### 🕹️ Solo mode: A tap of your wrist, and your little guy zips along! 🍒 Those pellets are waving hello—swerve left, zip right, don’t let those ghosts catch up! Munch, munch, keep that feast going nonstop～
![8月14日 (2)(5)](https://github.com/user-attachments/assets/fe460364-28c4-4ba0-a93c-0d761ce60dd3)
#### 👯 Multiplayer mode: Team up with your buddy and let the chaos begin! 👋 Your wrist sends your guy zipping; theirs guides their pal dashing. Snag pellets, playfully block each other—total hilarity! Who’ll be the first pellet-gobbling champ? Let the battle rage 🎉!

License

This project is open source under the MIT LICENSE - see license file for details.

Feel free to submit an Issue or PR to improve the gesture interaction system!
