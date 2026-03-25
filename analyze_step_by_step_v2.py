import os
import re
from datetime import datetime
from collections import defaultdict
import glob
import sys
import statistics

def parse_serial_from_filename(filename):
    """파일명에서 시리얼 번호 추출"""
    # 파일명 규칙이 여러 버전 존재:
    # - G5091W225C019_2025.12.12_19.32.41...
    # - G5091W2258015_2026.1.16_15.35.14...
    # 공통적으로 "시리얼_날짜..." 형태이므로 첫 '_' 앞을 시리얼로 사용
    base = os.path.basename(filename)
    serial = base.split("_", 1)[0]
    if serial.startswith("G5091W") or serial.startswith("G5091N"):
        return serial
    # 폴백: 혹시 '_'가 없거나 다른 형태면 정규식으로 한 번 더 시도
    match = re.search(r"(G5091[WN][^_]+)", base)
    return match.group(1) if match else None


def infer_process_type_from_serial(serial: str):
    """
    시리얼에서 OHT/OBS 타입을 판별.
    - OHT: 시리얼에 'W' 포함 (예: G5091W...)
    - OBS: 시리얼에 'N' 포함 (예: G5091N...)
    """
    if not serial:
        return None
    # 예: G5091W..., G5091N...
    if re.match(r"^G5091W", serial):
        return "OHT"
    if re.match(r"^G5091N", serial):
        return "OBS"
    return None

def parse_time_from_filename(filename):
    """파일명에서 타임스탬프 추출 (예: 2025.12.12_19.32.41 / 2026.1.16_15.35.14 / 20251212_1932)"""
    patterns = [
        r'(\d{4})\.(\d{1,2})\.(\d{1,2})_(\d{1,2})\.(\d{1,2})\.(\d{1,2})',  # 2026.1.16_15.35.14 (월/일 1~2자리)
        r'(\d{8})_(\d{4})',  # 20251212_1932
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            if len(match.groups()) == 6:
                year, month, day, hour, minute, second = match.groups()
                try:
                    return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                except:
                    pass
            elif len(match.groups()) == 2:
                date_str, time_str = match.groups()
                try:
                    return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
                except:
                    pass
    return None

def analyze_process_steps(base_path, process_type):
    """절차별 공정시간 분석 (파일명 시간 ~ 파일 수정 시간)"""
    
    step_paths = {
        '수평도검사': os.path.join(base_path, 'tx_level'),
        '홈포지션검사': os.path.join(base_path, 'home_position'),
        '거리성능검사': os.path.join(base_path, 'distance_test'),
        'OHT_LUT생성': os.path.join(base_path, 'OHT_filtering_table'),
        'OHT_검사': os.path.join(base_path, 'oht_filtering_validation'),
        'Rear_cover검사': os.path.join(base_path, 'rear_cover_test'),
        '최대거리검사': os.path.join(base_path, 'max_dist'),
    }

    # 각 절차에서 실제로 생성되는 파일 종류(확장자)를 포함해서 종료시간(max LastWriteTime)을 잡는다.
    # (GUI/스크립트 기준: zip 외에 png/csv/xlsx/txt 등이 추가 생성됨)
    step_file_exts = {
        '수평도검사': ['.zip', '.png'],
        '홈포지션검사': ['.zip', '.txt'],
        '거리성능검사': ['.zip', '.xlsx'],
        'OHT_LUT생성': ['.zip', '.png', '.csv'],
        'OHT_검사': ['.zip', '.xlsx'],
        'Rear_cover검사': ['.zip', '.xlsx'],
        '최대거리검사': ['.zip', '.xlsx'],
    }
    
    if process_type == 'OBS':
        step_paths.pop('OHT_LUT생성', None)
        step_paths.pop('OHT_검사', None)
        step_paths.pop('Rear_cover검사', None)
    
    results = defaultdict(lambda: defaultdict(dict))
    
    for step_name, step_path in step_paths.items():
        if not os.path.exists(step_path):
            continue
        
        # 해당 절차에서 생성되는 파일 모두 수집
        exts = step_file_exts.get(step_name, ['.zip'])
        step_files = []
        for ext in exts:
            step_files.extend(glob.glob(os.path.join(step_path, f'*{ext}')))
        
        # 시리얼별로 파일 그룹화 (+ 동일 공정 내 raw/proc 등 다중 파일 고려)
        # 공정 식별 키: 파일명에 포함된 시작 시각(start_time, test_time)
        serial_to_files = defaultdict(list)
        for fpath in step_files:
            serial = parse_serial_from_filename(os.path.basename(fpath))
            # OHT/OBS를 시리얼로 구분 (섞임 방지)
            if serial and infer_process_type_from_serial(serial) == process_type:
                serial_to_files[serial].append(fpath)

        # 각 시리얼별로 "마지막 공정" 1개만 사용
        # - 동일 공정에서 여러 파일이 생성되면: 그 중 max(LastWriteTime)를 종료시간으로 사용
        # - 같은 시리얼 재검사가 여러 번이면: 가장 늦게 저장된 공정을 선택
        for serial, files in serial_to_files.items():
            # start_time(datetime) -> end_mtime(max) 집계
            group_end_mtime = defaultdict(float)
            for f in files:
                start_time = parse_time_from_filename(os.path.basename(f))
                if not start_time:
                    continue
                try:
                    mtime = os.path.getmtime(f)
                except OSError:
                    continue
                if mtime > group_end_mtime[start_time]:
                    group_end_mtime[start_time] = mtime

            if not group_end_mtime:
                continue

            # 마지막 공정 선택: end_mtime이 가장 큰 그룹
            last_start_time, last_end_mtime = max(group_end_mtime.items(), key=lambda kv: kv[1])
            end_time = datetime.fromtimestamp(last_end_mtime)

            duration_minutes = (end_time - last_start_time).total_seconds() / 60

            # 음수/0 값 제거 (파일 복사/시간오류 방지)
            if duration_minutes > 0.001:
                results[serial][step_name] = {
                    'start_time': last_start_time,
                    'end_time': end_time,
                    'duration_minutes': duration_minutes,
                }
                
    return results

def print_results(results, process_type):
    """결과 출력"""
    print(f"\n{'='*80}")
    print(f"{process_type} 절차별 공정시간 분석 (파일명 시간 ~ 파일 수정 시간)")
    print(f"{'='*80}")
    
    step_stats = defaultdict(list)
    
    for serial, steps in results.items():
        for step_name, data in steps.items():
            if 'duration_minutes' in data:
                step_stats[step_name].append(data['duration_minutes'])
    
    print(f"\n{'절차명':<20} {'최소(분)':<12} {'중간값(분)':<12} {'최대(분)':<12} {'건수':<8} {'추정공정(분)':<12}")
    print(f"{'-'*80}")
    
    if process_type == 'OHT':
        step_order = ['수평도검사', '홈포지션검사', '거리성능검사', 'OHT_LUT생성', 'OHT_검사', 'Rear_cover검사', '최대거리검사']
    else:
        step_order = ['수평도검사', '홈포지션검사', '거리성능검사', '최대거리검사']
    
    total_estimated_time = 0
    
    for step_name in step_order:
        if step_name in step_stats and step_stats[step_name]:
            durations = step_stats[step_name]
            min_val = min(durations)
            med_val = statistics.median(durations)
            max_val = max(durations)
            count = len(durations)
            
            # 중간값을 추정 공정시간(대표값)으로 사용
            estimated = med_val
            total_estimated_time += estimated
            
            print(f"{step_name:<20} {min_val:<12.2f} {med_val:<12.2f} {max_val:<12.2f} {count:<8} {estimated:<12.2f}")
    
    print(f"{'-'*80}")
    print(f"총 추정 공정시간: {total_estimated_time:.2f}분 ({total_estimated_time/60:.2f}시간)")

    # 상세 정보 출력
    print(f"\n{'='*80}")
    print(f"{process_type} 시리얼별 상세 정보")
    print(f"{'='*80}")
    
    for serial in sorted(results.keys()):
        print(f"\n시리얼: {serial}")
        print(f"{'절차명':<20} {'시작시간':<20} {'종료시간':<20} {'소요시간(분)':<15}")
        print(f"{'-'*80}")
        
        for step_name in step_order:
            if step_name in results[serial]:
                data = results[serial][step_name]
                start_str = data['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                end_str = data['end_time'].strftime('%H:%M:%S')
                duration = data['duration_minutes']
                print(f"{step_name:<20} {start_str:<20} {end_str:<20} {duration:<15.2f}")

# 메인 실행
if __name__ == '__main__':
    # base_path = r"log-backup 251223 (A2 2차제작)"
    base_path = r"log"
    
    with open('step_by_step_analysis_v2.txt', 'w', encoding='utf-8') as f:
        import sys
        from io import StringIO
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        # OHT 분석
        oht_results = analyze_process_steps(base_path, 'OHT')
        print_results(oht_results, 'OHT')
        
        # OBS 분석
        obs_results = analyze_process_steps(base_path, 'OBS')
        print_results(obs_results, 'OBS')
        
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        print(output) # 콘솔 출력
        f.write(output) # 파일 저장
    
    print("\n분석 완료! 결과가 'step_by_step_analysis_v2.txt'에 저장되었습니다.")
