-- Enable RLS on the storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Allow authenticated users to upload files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'documentos');

CREATE POLICY "Allow authenticated users to select files"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'documentos');

CREATE POLICY "Allow authenticated users to delete files"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'documentos');

-- Create policies for service role (admin)
CREATE POLICY "Allow service role to manage files"
ON storage.objects
TO service_role
USING (true)
WITH CHECK (true); 