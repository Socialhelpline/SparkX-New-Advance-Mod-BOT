import asyncio
from imdbkit import IMDBKit
import logging

async def main():
    imdb = IMDBKit()
    try:
        # Check if search_movie is async
        if asyncio.iscoroutinefunction(imdb.search_movie):
            print("search_movie is async")
            res = await imdb.search_movie('avatar')
        else:
            print("search_movie is sync")
            # If it's sync, maybe we should call it normally or with to_thread
            res = await asyncio.to_thread(imdb.search_movie, 'avatar')
            
        print("Type:", type(res))
        if hasattr(res, 'titles'):
            print("Has titles attribute")
        if isinstance(res, list):
            print("Is list. Length:", len(res))
            if len(res) > 0:
                print("First element:", res[0])
                print("First element attributes:", dir(res[0]))
                print("First element title:", res[0].title)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
