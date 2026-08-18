import motor.motor_asyncio
from info import DATABASE_URI, DATABASE_NAME
from logging_helper import LOGGER

class GFilterDB:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.gfilters
        self.settings_col = self.db.gfilter_settings

    async def add_gfilter(self, keyword, text):
        keyword = keyword.lower().strip()
        await self.col.update_one(
            {'keyword': keyword}, 
            {'$set': {'text': text}}, 
            upsert=True
        )

    async def get_gfilter(self, keyword):
        keyword = keyword.lower().strip()
        return await self.col.find_one({'keyword': keyword})

    async def get_all_gfilters(self):
        cursor = self.col.find({})
        return await cursor.to_list(length=None)

    async def delete_gfilter(self, keyword):
        keyword = keyword.lower().strip()
        await self.col.delete_one({'keyword': keyword})

    async def delete_all_gfilters(self):
        await self.col.delete_many({})

    async def is_gfilter_enabled(self):
        settings = await self.settings_col.find_one({'id': 'settings'})
        if settings:
            return settings.get('enabled', True)
        return True

    async def toggle_gfilter(self, state: bool):
        await self.settings_col.update_one(
            {'id': 'settings'}, 
            {'$set': {'enabled': state}}, 
            upsert=True
        )

# Initialize
gfilter_db = GFilterDB(DATABASE_URI, DATABASE_NAME)
