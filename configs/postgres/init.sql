-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Blog posts table
CREATE TABLE IF NOT EXISTS blog_posts (
  id SERIAL PRIMARY KEY,
  slug VARCHAR(255) UNIQUE NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  excerpt TEXT,
  published_at DATE NOT NULL,
  tags TEXT[] DEFAULT '{}',
  url TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Full-text search vector
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('english', title || ' ' || content)
  ) STORED
);

-- Blog embeddings table for vector search
CREATE TABLE IF NOT EXISTS blog_embeddings (
  id SERIAL PRIMARY KEY,
  post_id INTEGER REFERENCES blog_posts(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
  created_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(post_id, chunk_index)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON blog_posts(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_posts_tags ON blog_posts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_blog_posts_search ON blog_posts USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_blog_embeddings_vector ON blog_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create index after inserting data for better performance
-- ALTER TABLE blog_embeddings ADD COLUMN embedding vector(1536);
-- CREATE INDEX ON blog_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
