import asyncio
from imdbkit import IMDBKit

async def main():
    imdb = IMDBKit()
    try:
        if asyncio.iscoroutinefunction(imdb.search_movie):
            print("search_movie is async")
            res = await imdb.search_movie('avatar')
        else:
            print("search_movie is sync")
            res = imdb.search_movie('avatar')
        print(type(res))
        if hasattr(res, 'titles'):
            print("Has titles attribute")
        if isinstance(res, list):
            print("Is list. First element type:", type(res[0]))
            print("First element attributes:", dir(res[0]))
            print("First element:", res[0])
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
