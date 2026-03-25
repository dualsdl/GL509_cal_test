import os
import re
from datetime import datetime
from collections import defaultdict
import glob

def parse_serial_from_filename(filename):
    """파일명에서 시리얼 번호 추출"""
    match = re.search(r'G5091[WN]\d+C\d+', filename)
    return match.group(0) if match else None

def parse_time_from_filename(filename):
    """파일명에서 타임스탬프 추출 (2025.12.12_19.32.41 형식)"""
    # 여러 패턴 시도
    patterns = [
        r'(\d{4})\.(\d{2})\.(\d{2})_(\d{2})\.(\d{2})\.(\d{2})',  # 2025.12.12_19.32.41
        r'(\d{8})_(\d{4})',  # 20251212_1932
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            if len(match.groups()) == 6:  # 첫 번째 패턴
                year, month, day, hour, minute, second = match.groups()
                try:
                    return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                except:
                    pass
            elif len(match.groups()) == 2:  # 두 번째 패턴
                date_str, time_str = match.groups()
                try:
                    return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
                except:
                    pass
    return None

def get_step_name_from_path(filepath):
    """파일 경로에서 절차명 추출"""
    if 'tx_level' in filepath:
        return '수평도검사'
    elif 'home_position' in filepath:
        return '홈포지션검사'
    elif 'distance_test' in filepath:
        return '거리성능검사'
    elif 'OHT_filtering_table' in filepath or 'oht_filtering_table' in filepath:
        return 'OHT_LUT생성'
    elif 'oht_filtering_validation' in filepath:
        return 'OHT_검사'
    elif 'rear_cover' in filepath:
        return 'Rear_cover검사'
    elif 'max_dist' in filepath:
        return '최대거리검사'
    return None

def analyze_process_steps(base_path, process_type):
    """절차별 공정시간 분석"""
    
    # 각 절차별 파일 경로
    step_paths = {
        '수평도검사': os.path.join(base_path, 'tx_level'),
        '홈포지션검사': os.path.join(base_path, 'home_position'),
        '거리성능검사': os.path.join(base_path, 'distance_test'),
        'OHT_LUT생성': os.path.join(base_path, 'OHT_filtering_table'),
        'OHT_검사': os.path.join(base_path, 'oht_filtering_validation'),
        'Rear_cover검사': os.path.join(base_path, 'rear_cover_test'),
        '최대거리검사': os.path.join(base_path, 'max_dist'),
    }
    
    # OBS는 OHT 전용 절차 제외
    if process_type == 'OBS':
        step_paths.pop('OHT_LUT생성', None)
        step_paths.pop('OHT_검사', None)
        step_paths.pop('Rear_cover검사', None)
    
    # 각 시리얼별로 절차별 파일 시간 수집
    serial_steps = defaultdict(lambda: defaultdict(list))
    
    for step_name, step_path in step_paths.items():
        if not os.path.exists(step_path):
            continue
        
        # zip 파일 찾기
        zip_files = glob.glob(os.path.join(step_path, '*.zip'))
        
        for zip_file in zip_files:
            serial = parse_serial_from_filename(os.path.basename(zip_file))
            file_time = parse_time_from_filename(os.path.basename(zip_file))
            
            if serial and file_time:
                serial_steps[serial][step_name].append((file_time, zip_file))
    
    # 각 시리얼별로 시간순 정렬 및 분석
    results = defaultdict(lambda: defaultdict(dict))
    
    for serial, steps in serial_steps.items():
        # 각 절차별로 가장 최근 파일 시간 사용
        step_times = {}
        for step_name, files in steps.items():
            if files:
                # 가장 최근 파일 시간 사용
                latest_file = max(files, key=lambda x: x[0])
                step_times[step_name] = latest_file[0]
        
        # 절차 순서 정의
        if process_type == 'OHT':
            step_order = ['수평도검사', '홈포지션검사', '거리성능검사', 'OHT_LUT생성', 'OHT_검사', 'Rear_cover검사', '최대거리검사']
        else:  # OBS
            step_order = ['수평도검사', '홈포지션검사', '거리성능검사', '최대거리검사']
        
        # 각 절차별 소요 시간 계산
        prev_time = None
        prev_step = None
        
        for step_name in step_order:
            if step_name in step_times:
                current_time = step_times[step_name]
                
                if prev_time is None:
                    # 첫 번째 절차 (수평도검사)는 2분 고정
                    duration_minutes = 2.0
                else:
                    # 이전 절차와의 시간 차이
                    duration_minutes = (current_time - prev_time).total_seconds() / 60
                
                results[serial][step_name] = {
                    'time': current_time,
                    'duration_minutes': duration_minutes,
                    'prev_step': prev_step
                }
                
                prev_time = current_time
                prev_step = step_name
    
    return results

def print_results(results, process_type):
    """결과 출력"""
    print(f"\n{'='*80}")
    print(f"{process_type} 절차별 공정시간 분석")
    print(f"{'='*80}")
    
    # 각 절차별 통계 계산
    step_stats = defaultdict(list)
    
    for serial, steps in results.items():
        for step_name, data in steps.items():
            if 'duration_minutes' in data:
                step_stats[step_name].append(data['duration_minutes'])
    
    # 전체 통계 출력
    print(f"\n{'절차명':<20} {'평균(분)':<12} {'최소(분)':<12} {'최대(분)':<12} {'건수':<8}")
    print(f"{'-'*80}")
    
    if process_type == 'OHT':
        step_order = ['수평도검사', '홈포지션검사', '거리성능검사', 'OHT_LUT생성', 'OHT_검사', 'Rear_cover검사', '최대거리검사']
    else:
        step_order = ['수평도검사', '홈포지션검사', '거리성능검사', '최대거리검사']
    
    for step_name in step_order:
        if step_name in step_stats:
            durations = step_stats[step_name]
            avg = sum(durations) / len(durations)
            min_val = min(durations)
            max_val = max(durations)
            count = len(durations)
            print(f"{step_name:<20} {avg:<12.2f} {min_val:<12.2f} {max_val:<12.2f} {count:<8}")
    
    # 상세 정보 출력
    print(f"\n{'='*80}")
    print(f"{process_type} 시리얼별 상세 정보")
    print(f"{'='*80}")
    
    for serial in sorted(results.keys()):
        print(f"\n시리얼: {serial}")
        print(f"{'절차명':<20} {'시간':<20} {'소요시간(분)':<15} {'이전절차':<20}")
        print(f"{'-'*80}")
        
        for step_name in step_order:
            if step_name in results[serial]:
                data = results[serial][step_name]
                time_str = data['time'].strftime('%Y-%m-%d %H:%M:%S') if data.get('time') else 'N/A'
                duration = data.get('duration_minutes', 0)
                prev = data.get('prev_step', '시작') or '시작'
                print(f"{step_name:<20} {time_str:<20} {duration:<15.2f} {prev:<20}")

# 메인 실행
if __name__ == '__main__':
    base_path = r"log-backup 251223 (A2 2차제작)"
    
    # OHT 분석
    print("\n" + "="*80)
    print("OHT 분석 시작")
    print("="*80)
    oht_results = analyze_process_steps(base_path, 'OHT')
    print_results(oht_results, 'OHT')
    
    # OBS 분석
    print("\n" + "="*80)
    print("OBS 분석 시작")
    print("="*80)
    obs_results = analyze_process_steps(base_path, 'OBS')
    print_results(obs_results, 'OBS')
    
    # 결과를 파일로 저장
    with open('step_by_step_analysis.txt', 'w', encoding='utf-8') as f:
        import sys
        from io import StringIO
        
        # OHT 결과 저장
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        print_results(oht_results, 'OHT')
        oht_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        f.write(oht_output)
        
        # OBS 결과 저장
        sys.stdout = StringIO()
        print_results(obs_results, 'OBS')
        obs_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        f.write(obs_output)
    
    print("\n분석 완료! 결과가 'step_by_step_analysis.txt'에 저장되었습니다.")

