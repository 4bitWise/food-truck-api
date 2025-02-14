#!/usr/bin/env python 3.12

from pymongo import MongoClient
from config import Settings

class AtlasClient():
    _atlas_client = None

    def __init__(self, altas_uri, dbname):
       if AtlasClient._atlas_client is not None:
            raise Exception("Use AtlasClient.get_instance() to get the unique instance !")

       self.mongodb_client = MongoClient(altas_uri)
       self.database = self.mongodb_client[dbname]

    def ping(self):
       self.mongodb_client.admin.command('ping')

    def get_collection(self, collection_name):
       collection = self.database[collection_name]
       return collection

    def find(self, collection_name, filter = {}, limit=0):
       collection = self.database[collection_name]
       items = list(collection.find(filter=filter, limit=limit))
       return items

    @classmethod
    def get_instance(cls, atlas_uri, dbname):
        if cls._atlas_client is None:
            if not atlas_uri or not dbname:
                raise ValueError("Les paramètres atlas_uri et dbname sont obligatoires pour la première initialisation")
            cls._atlas_client = cls(atlas_uri, dbname)
        return cls._atlas_client
