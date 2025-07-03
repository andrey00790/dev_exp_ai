"""Add comprehensive document metadata

Revision ID: 005_add_document_metadata
Revises: 004_add_sso_tables
Create Date: 2024-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_document_metadata'
down_revision = '004_add_sso_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавление расширенных метаданных для документов"""
    
    # Создание основной таблицы документов
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text()),
        
        # Метаданные источника
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('source_url', sa.String()),
        
        # Иерархия и связи
        sa.Column('parent_id', sa.String()),
        sa.Column('project_key', sa.String()),
        sa.Column('space_key', sa.String()),
        sa.Column('repository_name', sa.String()),
        
        # Категоризация
        sa.Column('document_type', sa.String()),
        sa.Column('category', sa.String()),
        sa.Column('tags', postgresql.JSON()),
        sa.Column('labels', postgresql.JSON()),
        
        # Авторство и версионность
        sa.Column('author', sa.String()),
        sa.Column('author_email', sa.String()),
        sa.Column('created_by', sa.String()),
        sa.Column('updated_by', sa.String()),
        sa.Column('assignee', sa.String()),
        
        # Временные метки
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('source_created_at', sa.DateTime()),
        sa.Column('source_updated_at', sa.DateTime()),
        sa.Column('last_synced_at', sa.DateTime()),
        
        # Статус и качество
        sa.Column('status', sa.String(), nullable=False, default='active'),
        sa.Column('priority', sa.String()),
        sa.Column('quality_score', sa.Float(), default=0.0),
        sa.Column('relevance_score', sa.Float(), default=0.0),
        
        # Технические метаданные
        sa.Column('language', sa.String(), default='en'),
        sa.Column('content_length', sa.Integer()),
        sa.Column('word_count', sa.Integer()),
        sa.Column('file_extension', sa.String()),
        sa.Column('file_size', sa.Integer()),
        sa.Column('encoding', sa.String()),
        
        # Дополнительные метаданные
        sa.Column('metadata', postgresql.JSON()),
        
        # Поисковые индексы
        sa.Column('search_vector', sa.Text()),
        sa.Column('embedding_vector', postgresql.JSON()),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание таблицы чанков документов
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        
        # Наследуем метаданные от родительского документа
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=False),
        
        # Позиция в документе
        sa.Column('start_position', sa.Integer()),
        sa.Column('end_position', sa.Integer()),
        
        # Векторное представление
        sa.Column('embedding_vector', postgresql.JSON()),
        
        # Качество чанка
        sa.Column('quality_score', sa.Float(), default=0.0),
        
        sa.Column('created_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    
    # Создание таблицы истории поиска
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('search_type', sa.String(), default='semantic'),
        sa.Column('filters_applied', postgresql.JSON()),
        sa.Column('results_count', sa.Integer(), default=0),
        sa.Column('search_time_ms', sa.Float()),
        sa.Column('sources_used', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание таблицы обратной связи по поиску
    op.create_table(
        'search_feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('search_id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('feedback_type', sa.String(), nullable=False),  # like, dislike, irrelevant, helpful
        sa.Column('comment', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    
    # Создание таблицы настроек источников для пользователей
    op.create_table(
        'user_search_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('enabled_sources', postgresql.JSON()),
        sa.Column('search_preferences', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Создание индексов для оптимизации поиска
    
    # Основные поисковые индексы
    op.create_index('idx_documents_source_type', 'documents', ['source_type'])
    op.create_index('idx_documents_source_name', 'documents', ['source_name'])
    op.create_index('idx_documents_source_id', 'documents', ['source_id'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    
    # Индексы для фильтрации
    op.create_index('idx_documents_project_key', 'documents', ['project_key'])
    op.create_index('idx_documents_space_key', 'documents', ['space_key'])
    op.create_index('idx_documents_repository_name', 'documents', ['repository_name'])
    op.create_index('idx_documents_document_type', 'documents', ['document_type'])
    op.create_index('idx_documents_category', 'documents', ['category'])
    op.create_index('idx_documents_author', 'documents', ['author'])
    op.create_index('idx_documents_language', 'documents', ['language'])
    op.create_index('idx_documents_priority', 'documents', ['priority'])
    
    # Временные индексы
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_documents_updated_at', 'documents', ['updated_at'])
    op.create_index('idx_documents_source_updated_at', 'documents', ['source_updated_at'])
    op.create_index('idx_documents_last_synced_at', 'documents', ['last_synced_at'])
    
    # Составные индексы для частых запросов
    op.create_index('idx_documents_source_type_name', 'documents', ['source_type', 'source_name'])
    op.create_index('idx_documents_status_updated', 'documents', ['status', 'updated_at'])
    op.create_index('idx_documents_category_quality', 'documents', ['category', 'quality_score'])
    
    # Полнотекстовый поисковый индекс
    op.execute("""
        CREATE INDEX idx_documents_fulltext 
        ON documents 
        USING gin(to_tsvector('english', title || ' ' || content))
    """)
    
    # Индексы для чанков
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_document_chunks_source_type', 'document_chunks', ['source_type'])
    op.create_index('idx_document_chunks_source_name', 'document_chunks', ['source_name'])
    
    # Индексы для истории поиска
    op.create_index('idx_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('idx_search_history_created_at', 'search_history', ['created_at'])
    op.create_index('idx_search_history_user_created', 'search_history', ['user_id', 'created_at'])
    
    # Индексы для обратной связи
    op.create_index('idx_search_feedback_user_id', 'search_feedback', ['user_id'])
    op.create_index('idx_search_feedback_document_id', 'search_feedback', ['document_id'])
    op.create_index('idx_search_feedback_type', 'search_feedback', ['feedback_type'])
    
    # GIN индексы для JSON полей (для быстрого поиска по тегам и метаданным)
    op.execute("CREATE INDEX idx_documents_tags_gin ON documents USING gin(tags)")
    op.execute("CREATE INDEX idx_documents_labels_gin ON documents USING gin(labels)")
    op.execute("CREATE INDEX idx_documents_metadata_gin ON documents USING gin(metadata)")
    
    # Создание функции для автоматического обновления поискового вектора
    op.execute("""
        CREATE OR REPLACE FUNCTION update_document_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = to_tsvector('english', NEW.title || ' ' || NEW.content);
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Создание триггера для автоматического обновления поискового вектора
    op.execute("""
        CREATE TRIGGER trigger_update_document_search_vector
        BEFORE INSERT OR UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION update_document_search_vector();
    """)
    
    # Создание функции для автоматического подсчета статистик
    op.execute("""
        CREATE OR REPLACE FUNCTION update_document_stats()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.content_length = LENGTH(NEW.content);
            NEW.word_count = array_length(string_to_array(NEW.content, ' '), 1);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Создание триггера для автоматического подсчета статистик
    op.execute("""
        CREATE TRIGGER trigger_update_document_stats
        BEFORE INSERT OR UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION update_document_stats();
    """)


def downgrade() -> None:
    """Откат миграции"""
    
    # Удаление триггеров
    op.execute("DROP TRIGGER IF EXISTS trigger_update_document_search_vector ON documents")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_document_stats ON documents")
    
    # Удаление функций
    op.execute("DROP FUNCTION IF EXISTS update_document_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS update_document_stats()")
    
    # Удаление таблиц в обратном порядке
    op.drop_table('user_search_preferences')
    op.drop_table('search_feedback')
    op.drop_table('search_history')
    op.drop_table('document_chunks')
    op.drop_table('documents') 