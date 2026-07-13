#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gestión de base de datos H2/SQLite de prompts y recursos.
Implementa almacenamiento, búsqueda y recuperación de prompts.
"""

import os
import sqlite3
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

# ================= CONFIGURACIÓN =================
DB_PATH = "./data/prompts.db"
# =================================================

class BaseVectorial:
    """Clase para gestión de base de datos de prompts (SQLite/H2 compatible)."""
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Inicializa la base de datos.
        
        Args:
            db_path: Ruta del archivo de base de datos
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Crear conexión y tablas
        self._init_db()
    
    def _init_db(self) -> None:
        """Inicializa la estructura de la base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de prompts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de tags
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            # Tabla de relación prompts-tags
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_tags (
                    prompt_id TEXT,
                    tag_id INTEGER,
                    PRIMARY KEY (prompt_id, tag_id),
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            """)
            
            # Índices para búsqueda
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompts_text 
                ON prompts(text)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompts_metadata 
                ON prompts(metadata)
            """)
            
            conn.commit()
    
    def add_prompt(
        self,
        prompt_id: str,
        text: str,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Agrega un prompt a la base de datos.
        
        Args:
            prompt_id: Identificador único del prompt
            text: Texto del prompt
            metadata: Metadatos adicionales (categoría, etc.)
            tags: Lista de tags asociados
        """
        if metadata is None:
            metadata = {}
        
        metadata_json = json.dumps(metadata)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insertar prompt
            cursor.execute("""
                INSERT OR REPLACE INTO prompts (id, text, metadata, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (prompt_id, text, metadata_json))
            
            # Procesar tags
            if tags:
                for tag in tags:
                    # Insertar tag si no existe
                    cursor.execute("""
                        INSERT OR IGNORE INTO tags (name) VALUES (?)
                    """, (tag,))
                    
                    # Obtener ID del tag
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                    tag_id = cursor.fetchone()[0]
                    
                    # Relacionar prompt con tag
                    cursor.execute("""
                        INSERT OR IGNORE INTO prompt_tags (prompt_id, tag_id)
                        VALUES (?, ?)
                    """, (prompt_id, tag_id))
            
            conn.commit()
    
    def search_prompts(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Busca prompts que coincidan con la consulta.
        
        Args:
            query: Texto de búsqueda
            n_results: Número de resultados a retornar
            category: Filtro por categoría
            tags: Filtro por tags
            
        Returns:
            Lista de resultados con prompts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Construir query base
            sql = """
                SELECT DISTINCT p.id, p.text, p.metadata, p.created_at, p.updated_at
                FROM prompts p
            """
            params = []
            
            # Joins para tags
            if tags:
                sql += """
                    JOIN prompt_tags pt ON p.id = pt.prompt_id
                    JOIN tags t ON pt.tag_id = t.id
                """
            
            sql += " WHERE p.text LIKE ?"
            params.append(f"%{query}%")
            
            # Filtro por categoría
            if category:
                sql += " AND p.metadata LIKE ?"
                params.append(f'%category%{category}%')
            
            # Filtro por tags
            if tags:
                tag_placeholders = ",".join(["?"] * len(tags))
                sql += f" AND t.name IN ({tag_placeholders})"
                params.extend(tags)
            
            sql += f" LIMIT {n_results}"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Formatear resultados
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'text': row['text'],
                    'metadata': json.loads(row['metadata']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return results
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """
        Obtiene un prompt por su ID.
        
        Args:
            prompt_id: Identificador del prompt
            
        Returns:
            Diccionario con el prompt o None si no existe
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.text, p.metadata, p.created_at, p.updated_at
                FROM prompts p
                WHERE p.id = ?
            """, (prompt_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Obtener tags
            cursor.execute("""
                SELECT t.name
                FROM tags t
                JOIN prompt_tags pt ON t.id = pt.tag_id
                WHERE pt.prompt_id = ?
            """, (prompt_id,))
            
            tag_rows = cursor.fetchall()
            tags = [row['name'] for row in tag_rows]
            
            return {
                'id': row['id'],
                'text': row['text'],
                'metadata': json.loads(row['metadata']),
                'tags': tags,
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """
        Elimina un prompt de la base de datos.
        
        Args:
            prompt_id: Identificador del prompt
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def update_prompt(
        self,
        prompt_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Actualiza un prompt existente.
        
        Args:
            prompt_id: Identificador del prompt
            text: Nuevo texto (opcional)
            metadata: Nuevos metadatos (opcional)
            tags: Nueva lista de tags (opcional)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Actualizar texto y metadata
                if text is not None or metadata is not None:
                    updates = []
                    params = []
                    
                    if text is not None:
                        updates.append("text = ?")
                        params.append(text)
                    
                    if metadata is not None:
                        updates.append("metadata = ?")
                        params.append(json.dumps(metadata))
                    
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    
                    sql = f"UPDATE prompts SET {', '.join(updates)} WHERE id = ?"
                    params.append(prompt_id)
                    
                    cursor.execute(sql, params)
                
                # Actualizar tags
                if tags is not None:
                    # Eliminar tags existentes
                    cursor.execute("""
                        DELETE FROM prompt_tags WHERE prompt_id = ?
                    """, (prompt_id,))
                    
                    # Agregar nuevos tags
                    for tag in tags:
                        cursor.execute("""
                            INSERT OR IGNORE INTO tags (name) VALUES (?)
                        """, (tag,))
                        
                        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                        tag_id = cursor.fetchone()[0]
                        
                        cursor.execute("""
                            INSERT OR IGNORE INTO prompt_tags (prompt_id, tag_id)
                            VALUES (?, ?)
                        """, (prompt_id, tag_id))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    def list_all_prompts(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Lista todos los prompts en la base de datos.
        
        Args:
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de todos los prompts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            sql = "SELECT id, text, metadata, created_at, updated_at FROM prompts"
            if limit:
                sql += f" LIMIT {limit}"
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'text': row['text'],
                    'metadata': json.loads(row['metadata']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return results
    
    def count_prompts(self) -> int:
        """
        Retorna el número total de prompts en la base.
        
        Returns:
            Número de prompts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM prompts")
            return cursor.fetchone()[0]
    
    def clear_collection(self) -> None:
        """Elimina todos los prompts de la base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prompts")
            cursor.execute("DELETE FROM prompt_tags")
            cursor.execute("DELETE FROM tags")
            conn.commit()
    
    def get_all_tags(self) -> List[str]:
        """
        Retorna todos los tags disponibles.
        
        Returns:
            Lista de tags
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM tags ORDER BY name")
            return [row[0] for row in cursor.fetchall()]


def main():
    """Ejemplo de uso de la base de datos."""
    # Inicializar base de datos
    base = BaseVectorial()
    
    # Agregar prompts de ejemplo
    print("Agregando prompts de ejemplo...")
    base.add_prompt(
        prompt_id="prompt_001",
        text="Analizar arquitectura de software para plataformas con bases de datos masivas",
        metadata={
            "categoria": "arquitectura",
            "prioridad": "alta"
        },
        tags=["software", "database", "architecture"]
    )
    
    base.add_prompt(
        prompt_id="prompt_002",
        text="Generar diagramas PlantUML para sistemas distribuidos",
        metadata={
            "categoria": "diagramas",
            "prioridad": "media"
        },
        tags=["plantuml", "distributed", "diagrams"]
    )
    
    base.add_prompt(
        prompt_id="prompt_003",
        text="Diseñar microservicios para aplicaciones escalables",
        metadata={
            "categoria": "microservicios",
            "prioridad": "alta"
        },
        tags=["microservices", "scalability", "kubernetes"]
    )
    
    # Buscar prompts
    print("\nBuscando prompts con 'arquitectura'...")
    results = base.search_prompts("arquitectura", n_results=2)
    
    for result in results:
        print(f"\nID: {result['id']}")
        print(f"Texto: {result['text']}")
        print(f"Metadatos: {result['metadata']}")
    
    # Listar todos los prompts
    print(f"\nTotal de prompts en la base: {base.count_prompts()}")
    
    # Obtener prompt específico
    print("\nObteniendo prompt específico...")
    prompt = base.get_prompt("prompt_001")
    if prompt:
        print(f"ID: {prompt['id']}")
        print(f"Texto: {prompt['text']}")
        print(f"Tags: {prompt['tags']}")
    
    # Listar todos los tags
    print(f"\nTags disponibles: {base.get_all_tags()}")


if __name__ == "__main__":
    main()
