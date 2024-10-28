# region SETUP
from PIL import Image
import pillow_heif
from PyPDF2 import PdfReader, PdfWriter
import os
import string
import subprocess
import ffmpeg

script_dir = os.path.dirname(os.path.abspath(__file__))
subfolder_name = "Output" #edit this to change where files output
subfolder_path = os.path.join(script_dir, subfolder_name)
os.makedirs(subfolder_path, exist_ok=True)
cd = os.path.dirname(os.path.abspath(__file__))
os.chdir(cd)
#endregion

#region FILE CONFIG
def findSuffix(filepath):
    base, extension = os.path.splitext(filepath)
    counter = 1
    
    while os.path.exists(filepath):
        filepath = f"{base}_{counter}{extension}"
        counter += 1
    
    return filepath

def base(filepath):
    basename, _ = os.path.splitext(filepath)
    return basename
#endregion

# region CONVERSION
def convert_image(input_file, output_file, output_format):
    pillow_heif.register_heif_opener()
    img = Image.open(input_file)
    
    if output_format.upper() == "JPG":
        target_format = "JPEG"
    else:
        target_format = output_format.upper()

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    img.save(output_file, format=target_format)

def convert_video(input_file, output_file, output_format):
    # Get playback speed modifier from user input
    speed = input("Enter playback speed modifier (enter for 1): ")

    # Default speed to 1 if no input is provided
    if not speed:
        speed = 1
    else:
        speed = float(speed)

    # Intermediate output file
    intermediate_file = 'temp_output.mp4'

    try:
        # Prepare the input stream
        input_stream = ffmpeg.input(input_file)

        # Adjust video playback speed for non-GIF formats
        if output_format.lower() != 'gif':
            video = input_stream.video.filter('setpts', f'1/{speed}*PTS')
            audio = input_stream.audio.filter('atempo', speed)  # Adjust audio tempo
            ffmpeg.output(video, audio, output_file).run()
        else:
            # For GIF, first convert to an intermediate video
            video = input_stream.video.filter('setpts', f'1/{speed}*PTS')
            ffmpeg.output(video, intermediate_file).run(overwrite_output=True)

            # Now convert the intermediate video to a GIF
            ffmpeg.input(intermediate_file).filter('fps', 10).output(output_file, format='gif', pix_fmt='rgb8').run(overwrite_output=True)

            # Optionally, remove the intermediate file
            os.remove(intermediate_file)

        print(f"Video converted successfully to {output_file} with playback speed {speed}.")
    except ffmpeg.Error as e:
        print(f"Error converting video: {e.stderr.decode()}")

def convert_audio(input_file, output_file, output_format):
    try:
        ffmpeg.input(input_file).output(output_file, format=output_format.lower()).run()
        print(f"Successfully converted {input_file} to {output_file}")
    except ffmpeg.Error as e:
        print(f"Error converting audio: {e}")

def convert_files(input_files, output_formats):
    for i, input_file in enumerate(input_files):
        output_format = output_formats[i]
        input_filename = os.path.basename(input_file)

        output_file = findSuffix(f"{subfolder_name}/{base(input_filename)}.{output_format}")    

        
        if output_format in ['JPG', 'PNG', 'HEIF']:
            convert_image(input_file, output_file, output_format)
        elif output_format in ['MOV', 'MP4', 'GIF']:
            convert_video(input_file, output_file, output_format)
        elif output_format == 'MP3':
            convert_audio(input_file, output_file, output_format)
        else:
            print("Unknown output format.")

def convert_mode():
    input_files = []
    output_formats = []
    count = 1

    print("Supported filetypes are PNG, JPG, HEIF, MP4, MOV, GIF, and MP3. \nPlease write the file path of the file you wish to convert, followed by the desired output format.")
    
    while True:
        input_file = input(f"File Path #{count}: ").strip()
        if input_file.lower() == "done" or input_file == "":
            break
        input_files.append(input_file)

        output_format = input(f"Output Format #{count}: ").strip().upper()
        if output_format.lower() == "done" or output_format == "":
            break
        output_formats.append(output_format)
        
        count += 1

    if os.access(subfolder_path, os.W_OK):
        print(f"Write access to {subfolder_path} is granted.")
    else:
        print(f"No write access to {subfolder_path}.")
    
    print("Converting...")
    convert_files(input_files, output_formats)
    print(f"Converted Successfully! Files are saved in {subfolder_path}")
#endregion

# region PDF
def insert_pdf_page(writer, insert_pdf, page_number):
    reader_insert = PdfReader(insert_pdf)
    
    original_pages = writer.pages[:page_number]
    remaining_pages = writer.pages[page_number:]
    
    new_writer = PdfWriter()
    for page in original_pages:
        new_writer.add_page(page)

    for page in reader_insert.pages:
        new_writer.add_page(page)

    for page in remaining_pages:
        new_writer.add_page(page)

    return new_writer

def PDF_mode():
    input_files = []
    page_indexes = []
    count = 1

    print("Please enter the file path of your base file")
    base_pdf_path = input().strip() 

    while True:
        input_file = input(f"File Path #{count}: ").strip()
        if input_file.lower() == "done" or input_file == "":
            break
        input_files.append(input_file)

        page_number = input("Merge to page (enter a number or leave blank for end): ").strip()
        if page_number == "":
            page_indexes.append(-1)
        else:
            page_indexes.append(int(page_number))

        count += 1

    writer = PdfWriter()

    base_reader = PdfReader(base_pdf_path)
    for page in base_reader.pages:
        writer.add_page(page)

    for i, input_file in enumerate(input_files):
        page_index = page_indexes[i]
        
        if page_index == -1:  
            page_index = len(writer.pages)
        
        writer = insert_pdf_page(writer, input_file, page_index)

        output_file = findSuffix(f"{subfolder_name}/{base(base_pdf_path)}_(edited).pdf")    
        with open(output_file, 'wb') as output_pdf:
            writer.write(output_pdf)

    print(f"Merging Successful! Output file path is: {output_file}")
#endregion

#region AUDIO/VISUAL
def merge_audio(audio_paths, output_file):
    with open("temp_audio_list.txt", "w") as f:
        for audio in audio_paths:
            f.write(f"file '{audio}'\n")

    try:
        ffmpeg.input('temp_audio_list.txt', format='concat', safe=0).output(output_file).run()
        print(f"Successfully merged audio files into {output_file}")
    except ffmpeg.Error as e:
        print(f"Error merging audio files: {e}")

    os.remove("temp_audio_list.txt")

def merge_video(video_paths, output_file):
    with open("temp_video_list.txt", "w") as f:
        for video in video_paths:
            f.write(f"file '{video}'\n")

    try:
        ffmpeg.input('temp_video_list.txt', format='concat', safe=0).output(output_file).run()
        print(f"Successfully merged video files into {output_file}")
    except ffmpeg.Error as e:
        print(f"Error merging video files: {e}")

    os.remove("temp_video_list.txt")

def VA_mode():
    user_input = input("Video or Audio? [V/A]: ").strip().upper()
    if user_input == "A":
        audio_paths = []
        audio_speeds = []
        while True:
            audio_path = input("Enter next audio path or enter to continue: ")
            if audio_path:
                audio_paths.append(audio_path)
            else:
                break

        if audio_paths:
            output_file = findSuffix(f"{subfolder_name}/{base(audio_paths[0])}_appended.mp3")    
            merge_audio(audio_paths, output_file)
    else:
        video_paths = []
        video_speeds = []
        while True:
            video_path = input("Enter next video path (.mp4 only) or enter to continue: ")
            if video_path:
                video_paths.append(video_path)
            else:
                break

        if video_paths:
            output_file = findSuffix(f"{subfolder_name}/{base(video_paths[0])}_appended.mp4")    
            merge_video(video_paths, output_file)
#endregion

#region ISOLATE/ADD
def isolate_audio(video_path, output_video_file, output_audio_file):
    try:
        audio_stream = ffmpeg.input(video_path).output(output_audio_file).run()
        video_stream = ffmpeg.input(video_path).output(output_video_file, an=None).run()

        print(f"Audio isolated successfully: {output_audio_file}")
        print(f"Video without audio created successfully: {output_video_file}")
    except ffmpeg.Error as e:
        print(f"Error isolating audio or creating video without audio: {e.stderr.decode('utf-8')}")

def get_gif_fps(gif_path):
    """Extracts the frame rate (fps) from the input GIF using ffprobe."""
    probe = ffmpeg.probe(gif_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    
    if video_stream and 'r_frame_rate' in video_stream:
        num, denom = map(int, video_stream['r_frame_rate'].split('/'))
        return num / denom if denom else 15
    return 15

def add_audio_to_video(video_path, audio_path, output_video_file, audio_loops=False, audio_speed=1.0):
    try:
        is_gif = video_path.lower().endswith('.gif')
        
        if is_gif:
            video = ffmpeg.input(video_path, f='gif')
            video = video.output('temp_video.mp4', vcodec='libx264', pix_fmt='yuv420p').run()
            video = ffmpeg.input('temp_video.mp4')
        else:
            video = ffmpeg.input(video_path)

        audio = ffmpeg.input(audio_path)

        if audio_speed != 1.0:
            audio = audio.filter('atempo', audio_speed)

        if audio_loops:
            audio = audio.filter('aloop', loop=-1, size=2**31-1)

        output_kwargs = {'vcodec': 'libx264', 'acodec': 'aac', 'shortest': None}
        
        if is_gif:
            fps = get_gif_fps(video_path)
            output_kwargs.update({
                'vf': f'fps={fps}',
                'loop': 0
            })

        ffmpeg.output(video, audio, output_video_file, **output_kwargs).run()        
        print(f"Audio added to video successfully: {output_video_file}")

        if is_gif:
            os.remove('temp_video.mp4')

    except ffmpeg.Error as e:
        print(f"Error adding audio to video: {e.stderr.decode('utf-8')}")

def isolate_mode():
    user_input = input("Isolate or add audio? [I/A]: ").strip().upper()
    
    if user_input == 'I':
        video_paths = []
        while True:
            video_path = input("Enter next video path or enter to continue: ")
            if video_path:
                video_paths.append(video_path)
            else:
                break
        
        for video_path in video_paths:
            output_video_file = findSuffix(f"{subfolder_name}/{base(video_path)}.mp4")
            output_audio_file = findSuffix(f"{subfolder_name}/{base(video_path)}_audio.mp3")
            isolate_audio(video_path, output_video_file, output_audio_file)
    
    else:
        video_path = ""
        audio_loops = True
        audio_speed = 1

        video_path = input("Enter next video path or enter to continue: ")
        audio_path = input("Enter audio path: ")
        user_input = input("Loop audio? [Enter/n]: ")
        audio_loops = user_input == ""
        user_input = input("Audio playback speed (enter for 1.0): ")
        if user_input: audio_speed = user_input

        output_file = findSuffix(f"{subfolder_name}/{base(video_path)}_{base(audio_path)}.mp4")

        add_audio_to_video(video_path, audio_path, output_file, audio_loops, audio_speed)
        
def Main():
    print("Welcome to the image/pdf conversion tool. Please select a mode:\n 1. Convert\n 2. PDF\n 3. Merge Audio/Video\n 4. Isolate/Add Audio")
    user_input = input("Enter mode number here: ").strip().upper()

    if user_input == "1":
        convert_mode()
    elif user_input == "2":
        PDF_mode()
    elif user_input == "3":
        VA_mode()
    else : isolate_mode()

    if os.access(subfolder_path, os.R_OK):
        subprocess.Popen(["open", subfolder_path])  # macOS specific
#endregion

#region MAIN
while True:
    Main()
    if input("Press enter to restart, or press any key to exit").lower():
        break

print("Thanks for using!")
exit()
#endregion
