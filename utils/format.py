

def format_seconds(seconds:int):
    # Chia số giây thành giờ, phút và giây
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    # Định dạng thành chuỗi "giờ:phút:giây"
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    return formatted_time

def seconds_to_hms(seconds: int):
    total_seconds = seconds * 60  # Chuyển đổi thành số giây
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"