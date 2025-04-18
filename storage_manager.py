import os
from firebase_config import bucket
from werkzeug.utils import secure_filename

class StorageManager:
    @staticmethod
    def upload_file(file, user_id, filename):
        """
        Faz upload de um arquivo para o Firebase Storage
        
        Args:
            file: O arquivo a ser enviado
            user_id: ID do usuário
            filename: Nome do arquivo
            
        Returns:
            str: URL pública do arquivo
        """
        # Criar um caminho seguro para o arquivo
        safe_filename = secure_filename(filename)
        file_path = f"users/{user_id}/{safe_filename}"
        
        # Fazer upload do arquivo
        blob = bucket.blob(file_path)
        blob.upload_from_file(file)
        
        # Tornar o arquivo público
        blob.make_public()
        
        # Retornar a URL pública
        return blob.public_url
    
    @staticmethod
    def delete_file(file_path):
        """
        Exclui um arquivo do Firebase Storage
        
        Args:
            file_path: Caminho do arquivo no Storage
        """
        try:
            blob = bucket.blob(file_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"Erro ao excluir arquivo: {str(e)}")
            return False
    
    @staticmethod
    def get_file_url(file_path):
        """
        Obtém a URL pública de um arquivo
        
        Args:
            file_path: Caminho do arquivo no Storage
            
        Returns:
            str: URL pública do arquivo
        """
        blob = bucket.blob(file_path)
        return blob.public_url 