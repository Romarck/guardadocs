import os
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from pathlib import Path

class StorageService:
    def __init__(self):
        if settings.STORAGE_TYPE == "s3":
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.AWS_BUCKET_NAME
        else:
            self.upload_folder = Path(settings.UPLOAD_FOLDER)
            self.upload_folder.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: BinaryIO, filename: str) -> str:
        if settings.STORAGE_TYPE == "s3":
            return await self._save_to_s3(file, filename)
        return await self._save_to_local(file, filename)

    async def _save_to_s3(self, file: BinaryIO, filename: str) -> str:
        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                filename
            )
            return f"s3://{self.bucket_name}/{filename}"
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    async def _save_to_local(self, file: BinaryIO, filename: str) -> str:
        file_path = self.upload_folder / filename
        with open(file_path, "wb") as buffer:
            content = file.read()
            buffer.write(content)
        return str(file_path)

    async def get_file(self, file_path: str) -> Optional[BinaryIO]:
        if settings.STORAGE_TYPE == "s3":
            return await self._get_from_s3(file_path)
        return await self._get_from_local(file_path)

    async def _get_from_s3(self, file_path: str) -> Optional[BinaryIO]:
        try:
            bucket, key = file_path.replace("s3://", "").split("/", 1)
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"]
        except ClientError:
            return None

    async def _get_from_local(self, file_path: str) -> Optional[BinaryIO]:
        path = Path(file_path)
        if not path.exists():
            return None
        return open(path, "rb")

    async def delete_file(self, file_path: str) -> bool:
        if settings.STORAGE_TYPE == "s3":
            return await this._delete_from_s3(file_path)
        return await this._delete_from_local(file_path)

    async def _delete_from_s3(self, file_path: str) -> bool:
        try:
            bucket, key = file_path.replace("s3://", "").split("/", 1)
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    async def _delete_from_local(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception:
            return False 