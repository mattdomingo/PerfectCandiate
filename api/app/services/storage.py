"""
Storage service for handling file uploads and downloads using MinIO
"""
import os
import aiofiles
from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional, BinaryIO
import uuid
from datetime import timedelta

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "resumes")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
    
    async def ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists, create if it doesn't"""
        try:
            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    async def upload_file(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: str = "application/octet-stream",
        folder: str = "uploads"
    ) -> str:
        """
        Upload a file to storage
        
        Args:
            file_data: File data as bytes
            filename: Original filename
            content_type: MIME type of the file
            folder: Folder to store the file in
            
        Returns:
            str: Object name (path) in storage
        """
        try:
            # Generate unique object name
            file_extension = os.path.splitext(filename)[1]
            object_name = f"{folder}/{uuid.uuid4()}{file_extension}"
            
            # Upload file
            self.client.put_object(
                self.bucket_name,
                object_name,
                data=file_data,
                length=len(file_data),
                content_type=content_type
            )
            
            logger.info(f"Uploaded file: {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(self, object_name: str) -> bytes:
        """
        Download a file from storage
        
        Args:
            object_name: Object name (path) in storage
            
        Returns:
            bytes: File data
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def get_presigned_url(
        self, 
        object_name: str, 
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get a presigned URL for file download
        
        Args:
            object_name: Object name (path) in storage
            expires: URL expiration time
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    async def delete_file(self, object_name: str) -> None:
        """
        Delete a file from storage
        
        Args:
            object_name: Object name (path) in storage
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    async def list_files(self, prefix: str = "") -> list:
        """
        List files in storage with optional prefix
        
        Args:
            prefix: Prefix to filter files
            
        Returns:
            list: List of object names
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    async def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            object_name: Object name (path) in storage
            
        Returns:
            bool: True if file exists
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
