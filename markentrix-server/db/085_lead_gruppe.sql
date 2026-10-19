-- Branchengruppe aus Lead-Listen (zum Filtern)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS gruppe text;
