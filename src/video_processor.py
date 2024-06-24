import cv2
import ffmpeg
import easyocr
from . import utils
import re

def point_to_dict(point):
    return {'x' : int(point[0]), 'y': int(point[1])}

def bbox_to_dict(bbox):
    x1, y1 = bbox[0]
    x2, y2 = bbox[1]
    x3, y3 = bbox[2]
    x4, y4 = bbox[3]
    return {'lt': point_to_dict(bbox[0]), 'rt': point_to_dict(bbox[1]), 'rb' : point_to_dict(bbox[2]), 'lb' : point_to_dict(bbox[3])}

class VideoProcessor:
    def __init__(self, source_video_path):
        self.source_video_path = source_video_path
        self.video_info = self.get_video_info()
        self.reader = easyocr.Reader(['en'], gpu=True, model_storage_directory='model/.', user_network_directory='model/.',)
        self.result_dict = {}
        self.m_interval = 5 # analysis a frame every 5 seconds
        self.m_fontsize_min_thres = 12
        self.m_fontsize_diff_thres = 5
        self.m_location_y_diff_thres = 0.1
    

    def get_video_info(self):
        probe = ffmpeg.probe(self.source_video_path)
        print('source_video_path: {}'.format(self.source_video_path))
        format = probe['format']
        bit_rate = int(format['bit_rate'])/1000
        duration = format['duration']
        size = int(format['size'])/1024/1024
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            print('No video stream found!')
            return
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        num_frames = int(video_stream['nb_frames'])
        fps = int(video_stream['r_frame_rate'].split('/')[0])/int(video_stream['r_frame_rate'].split('/')[1])
        duration = float(video_stream['duration'])
        return {
            'width': width,
            'height': height,
            'num_frames': num_frames,
            'bit_rate': bit_rate,
            'fps': fps,
            'size': size,
            'duration': duration
        }

    @staticmethod
    def calculate_bbox_area(bbox):
        # bbox is in the format [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        x1, y1 = bbox[0]
        x2, y2 = bbox[1]
        x3, y3 = bbox[2]
        x4, y4 = bbox[3]
        
        # Assuming the bbox is a rectangle, calculate the area
        width = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        height = ((x3 - x2) ** 2 + (y3 - y2) ** 2) ** 0.5
        area = width * height
        return area
    
    @staticmethod
    def calculate_bbox_location(bbox):
        x1, y1 = bbox[0]
        x2, y2 = bbox[1]
        x3, y3 = bbox[2]
        x4, y4 = bbox[3]
        m_x = (x1 + x2) / 2.0
        m_y = (y1 + y3) / 2.0
        return m_x, m_y
    
    def merge_bbox(self, bbox1, bbox2):
        all_points = bbox1 + bbox2
        # Find the min and max x and y values
        min_x = min(point[0] for point in all_points)
        min_y = min(point[1] for point in all_points)
        max_x = max(point[0] for point in all_points)
        max_y = max(point[1] for point in all_points)
        
        # Define the combined bbox
        merged_bbox = [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
        return merged_bbox


    
    

    def is_merge(self, text1, text2):
        is_same_size = abs(text1['fontsize'] - text2['fontsize']) < self.m_fontsize_diff_thres
        if not is_same_size:
            return False
        # y-coord difference no more than the character height
        delta_height_thres = text2['bbox'][2][1] - text2['bbox'][1][1]
        _, location_y1 = self.calculate_bbox_location(text1['bbox'])
        _, location_y2 = self.calculate_bbox_location(text2['bbox'])
        if location_y1 < location_y2:
            _, bottom_y1 = text1['bbox'][2]
            _, top_y2 = text2['bbox'][0]
            delta_y = top_y2 - bottom_y1
            return delta_y < delta_height_thres
        else:
            _, bottom_y2 = text2['bbox'][2]
            _, top_y1 = text1['bbox'][0]
            delta_y = top_y1 - bottom_y2
            return delta_y < delta_height_thres

    def calculate_font_size(self, text, bbox):
        mean_character_width = float(self.calculate_bbox_area(bbox) / len(text)) ** 0.5  
        canvas_width = self.video_info['width']
        return 1000 * mean_character_width / float(canvas_width)

    
    def merge(self, text1, text2):
        merged_text = text1['text'] + ' ' + text2['text']
        merged_bbox = self.merge_bbox(text1['bbox'], text2['bbox'])
        avg_font_size = (text1['fontsize'] + text2['fontsize']) / 2.0
        return {'text':merged_text, 'bbox': merged_bbox, 'fontsize': avg_font_size}
    
    
    def text_list_to_dict(self, tl):
        ret = {}
        index = 0
        for item in tl:
            ret[str(index)] = {'text': item['text'], 'bbox' : bbox_to_dict(item['bbox']), 'fontsize': int(item['fontsize']), 'is_title' : 0}
            index += 1
        return ret


    def process_frame(self, frame, pts):
        result = self.reader.readtext(frame, height_ths=1.0, width_ths=1.0)
        text_list = []
        for (bbox, text, prob) in result:
            cur_font_size = self.calculate_font_size(text, bbox)
            cur_text = {'text':text, 'bbox': bbox, 'fontsize': cur_font_size}

            if cur_font_size < self.m_fontsize_min_thres:
                continue
            if len(text_list) == 0:
                text_list.append(cur_text)
            else:
                pre_text = text_list[-1]
                if self.is_merge(pre_text, cur_text):
                    text_list[-1] = self.merge(pre_text, cur_text)
                else:
                    text_list.append(cur_text)


        if len(text_list) == 0:
            return
        
        cur_merged_text = " ".join(item['text'] for item in text_list)

        cur_len = len(self.result_dict)
        remove_chars = '[0-9’!"#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}~1.\'`-]+'
        temp = re.sub(remove_chars," ",cur_merged_text)
        if len(temp) < 20:
            return
        
        if len(self.result_dict) == 0:
            self.result_dict[str(cur_len)] = {'ocrlist':self.text_list_to_dict(text_list), 'pts':pts}
        else:
            pre_text_list = self.result_dict[str(cur_len-1)]['ocrlist'].values()
            pre_merged_text = " ".join(item ['text'] for item in pre_text_list)
            if utils.is_similar(pre_merged_text, cur_merged_text):
                self.result_dict[str(cur_len-1)] = {'ocrlist':self.text_list_to_dict(text_list), 'pts':pts} #use frame behind
            else:
                self.result_dict[str(cur_len)] = {'ocrlist':self.text_list_to_dict(text_list), 'pts':pts}
                img_path = 'save/frame_' + "{:.2f}".format(self.last_pts) + '.jpg'
                img = cv2.imwrite(img_path, self.last_frame)
                self.result_dict[str(cur_len-1)]['img'] = img_path
        
        self.last_frame = frame
        self.last_pts = pts

    def postprocess(self):
        # draw bbox for ocr result
        thickness = 2
        for v in self.result_dict.values():
            img_path = v['img']
            image = cv2.imread(img_path)
            ocr_list = v['ocrlist']
            max_fontsize = max(item["fontsize"] for item in ocr_list.values())
            for item in ocr_list.values():
                color = (0, 255, 0)  # 绿色
                bbox = item["bbox"]
                fontsize = item["fontsize"]
                if fontsize == max_fontsize:
                    color = (0, 0, 255)
                    item["is_title"] = 1
                points = [
                    (bbox["lt"]["x"], bbox["lt"]["y"]),
                    (bbox["rt"]["x"], bbox["rt"]["y"]),
                    (bbox["rb"]["x"], bbox["rb"]["y"]),
                    (bbox["lb"]["x"], bbox["lb"]["y"])
                ]
                for i in range(4):
                    start_point = points[i]
                    end_point = points[(i + 1) % 4]
                    cv2.line(image, start_point, end_point, color, thickness)
            cv2.imwrite(img_path, image)




    def process(self):
        if not self.video_info:
            return
        video_cap = cv2.VideoCapture(self.source_video_path)
        next_capture_time = 0
        while True:
            success, frame = video_cap.read()
            if success:
                pts = video_cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                if pts >= next_capture_time:
                    self.process_frame(frame, pts)
                    next_capture_time += self.m_interval
            else:
                break
        img_path = 'save/frame_' + "{:.2f}".format(self.last_pts) + '.jpg'
        img = cv2.imwrite(img_path, self.last_frame)
        self.result_dict[str(len(self.result_dict)-1)]['img'] = img_path
        print(self.result_dict)
        self.postprocess()
        video_cap.release()
    


if __name__ == "__main__":
    video_path = 'uploads\index.mp4'
    processor = VideoProcessor(video_path)
    processor.process()
