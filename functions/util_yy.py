import pickle
import zipfile
import os
import cv2
import math
import numpy as np

import json
import ast


def load_pickle_from_zip(zip_path: str):
    """
    zip_path: 압축 파일의 경로
    리턴: 압축 파일 내 pickle 데이터
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # 압축 파일 내에 있는 파일 목록을 가져옵니다.
        file_list = zf.namelist()
        if not file_list:
            raise ValueError("ZIP 파일이 비어있습니다.")
        # 파일이 하나만 있다고 가정하고 첫번째 파일을 선택
        file_name = file_list[0]
        with zf.open(file_name, 'r') as f:
            data = pickle.load(f)
    return data


def save_pickle_to_zip(data, path: str, filename: str):
    """
    data: 저장할 pickle 데이터
    zip_path: 저장할 압축 파일의 경로
    """
    import tempfile

    # 만약 경로에 폴더가 없다면 생성
    os.makedirs(path, exist_ok=True)

    # 임시 파일에 pickle 저장 후 zip에 추가 (대용량 pickle 대응)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_pickle:
        pickle.dump(data, tmp_pickle)
        tmp_pickle_path = tmp_pickle.name

    zip_path = os.path.join(path, f"{filename}.zip")
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        allowZip64=True,
        compresslevel=6
    ) as zf:
        zf.write(tmp_pickle_path, arcname=f"{filename}.pickle")

    # 임시 파일 삭제
    os.remove(tmp_pickle_path)


def draw_dashed_line(img, pt1, pt2, color=(0, 102, 51), thickness=1, dash_length=5, gap_length=3):
    """
    pt1 -> pt2를 잇는 '대시(dash) 라인'을 그립니다.
    - img: 그릴 대상 이미지 (numpy array)
    - pt1, pt2: 시작점, 끝점 좌표 (x, y)
    - color: BGR 색상 (예: (0,255,0))
    - thickness: 선 두께
    - dash_length: 대시가 실제로 그려지는 선분 길이 (픽셀)
    - gap_length: 대시 사이사이 공백 길이 (픽셀)
    """
    dist = math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])  # 두 점 사이의 거리
    if dist == 0:
        return  # 시작점과 끝점이 같다면 그릴 필요 없음

    # (dx, dy): pt1->pt2 방향 단위벡터
    dx = (pt2[0] - pt1[0]) / dist
    dy = (pt2[1] - pt1[1]) / dist

    # (dash + gap)씩 건너뛰며 반복
    step = dash_length + gap_length
    # np.arange(0, dist, step) -> 0, step, 2*step, ...
    for i in np.arange(0, dist, step):
        start = i
        end = i + dash_length  # 실제로 그리는 구간은 dash_length
        if end > dist:
            end = dist  # 직선 길이를 넘어가면 클리핑

        x1 = pt1[0] + dx * start
        y1 = pt1[1] + dy * start
        x2 = pt1[0] + dx * end
        y2 = pt1[1] + dy * end

        # 대시 구간만 선 그리기
        cv2.line(img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)


def rotate_points(x, y, angle_degrees):
    # 각도를 라디안으로 변환
    angle_radians = math.radians(-angle_degrees)

    # 회전 행렬 생성
    rotation_matrix = np.array([
        [math.cos(angle_radians), -math.sin(angle_radians)],
        [math.sin(angle_radians), math.cos(angle_radians)]
    ])

    # x, y 배열을 결합하여 점 배열로 생성
    points = np.vstack((x, y)).T

    # 회전 변환 적용
    rotated_points = np.dot(points, rotation_matrix.T)

    # 회전된 x, y 좌표 분리
    x_rotated, y_rotated = rotated_points[:, 0], rotated_points[:, 1]

    return x_rotated, y_rotated


def parse_dict_from_string(value):
    """
    문자열이 파이썬 형식의 list/dict 또는 JSON 형식이면 안전하게 파싱하여 반환.
    아니면 그대로 반환.
    """
    if not isinstance(value, str):
        return value

    # 먼저 JSON 형식으로 파싱 시도
    try:
        parsed = json.loads(value)
        if isinstance(parsed, (dict, list)):
            return parsed
    except json.JSONDecodeError:
        pass

    # JSON 파싱 실패시 파이썬 리터럴로 파싱 시도
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (dict, list)):
            return parsed
    except (ValueError, SyntaxError):
        pass

    return value