from . import check_caption_availability
from . import count_downloads
from . import count_liked_by
from . import delete_videos
from . import make_celebrities_tokens
from . import make_jasrac_tsv
from . import set_video
from . import update_all_series

if __name__ == '__main__':
    print('what are u gonna do?: ')
    print('1. Check caption availability')
    print('2. Count downloads')
    print('3. Count liked by')
    print('4. Delete videos')
    print('5. Make celebrities tokens')
    print('6. Make JASRAC tsv')
    print('7. Set video')
    print('8. Update all series')
    choice = input("Enter your choice (1 - 8): ")
    
    if choice == '1':
        check_caption_availability.main()
    elif choice == '2':
        count_downloads.main()
    elif choice == '3':
        count_liked_by.main()
    elif choice == '4':
        delete_videos.main()
    elif choice == '5':
        make_celebrities_tokens.main()
    elif choice == '6':
        make_jasrac_tsv.main()
    elif choice == '7':
        set_video.main()
    elif choice == '8':
        update_all_series.main()
