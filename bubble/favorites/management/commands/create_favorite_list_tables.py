from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import DatabaseError, connection

User = get_user_model()


class Command(BaseCommand):
    help = "Create FavoriteList tables manually"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("Creating FavoriteList table...")

            # Create the FavoriteList table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites_favoritelist (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    user_id INTEGER NOT NULL
                        REFERENCES users_user(id) ON DELETE CASCADE,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """)

            # Create the many-to-many table for shared_with
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites_favoritelist_shared_with (
                    id SERIAL PRIMARY KEY,
                    favoritelist_id INTEGER NOT NULL
                        REFERENCES favorites_favoritelist(id)
                        ON DELETE CASCADE,
                    user_id INTEGER NOT NULL
                        REFERENCES users_user(id) ON DELETE CASCADE,
                    UNIQUE(favoritelist_id, user_id)
                );
            """)

            # Create the many-to-many table for editors
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites_favoritelist_editors (
                    id SERIAL PRIMARY KEY,
                    favoritelist_id INTEGER NOT NULL
                        REFERENCES favorites_favoritelist(id)
                        ON DELETE CASCADE,
                    user_id INTEGER NOT NULL
                        REFERENCES users_user(id) ON DELETE CASCADE,
                    UNIQUE(favoritelist_id, user_id)
                );
            """)

            self.stdout.write(
                "Adding favorite_list_id column to favorites_favorite table..."
            )

            # Add the favorite_list_id column to the existing favorites_favorite table
            try:
                cursor.execute("""
                    ALTER TABLE favorites_favorite
                    ADD COLUMN favorite_list_id INTEGER;
                """)
                self.stdout.write("Column added successfully")
            except DatabaseError as e:
                if "already exists" in str(e):
                    self.stdout.write("Column already exists, skipping...")
                else:
                    self.stdout.write(f"Error adding column: {e}")

            # Create the foreign key constraint
            try:
                cursor.execute("""
                    ALTER TABLE favorites_favorite
                    ADD CONSTRAINT favorites_favorite_favorite_list_id_fkey
                    FOREIGN KEY (favorite_list_id)
                        REFERENCES favorites_favoritelist(id)
                        ON DELETE CASCADE;
                """)
                self.stdout.write("Foreign key constraint added successfully")
            except DatabaseError as e:
                if "already exists" in str(e):
                    self.stdout.write(
                        "Foreign key constraint already exists, skipping..."
                    )
                else:
                    self.stdout.write(f"Error adding foreign key: {e}")

            self.stdout.write("Creating default favorite lists for existing users...")

            # Create default favorite lists for all existing users
            users = User.objects.all()
            for user in users:
                try:
                    cursor.execute(
                        """
                        INSERT INTO favorites_favoritelist
                        (name, user_id, is_default, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW());
                    """,
                        ["My Favorites", user.id, True],
                    )
                    self.stdout.write(f"Created default list for user {user.username}")
                except DatabaseError as e:
                    self.stdout.write(
                        f"Error creating default list for user {user.username}: {e}"
                    )

            self.stdout.write("Updating existing favorites to use default lists...")

            # Update existing favorites to use the default lists
            try:
                cursor.execute("""
                    UPDATE favorites_favorite
                    SET favorite_list_id = (
                        SELECT id FROM favorites_favoritelist
                        WHERE favorites_favoritelist.user_id =
                            favorites_favorite.user_id
                        AND favorites_favoritelist.is_default = TRUE
                        LIMIT 1
                    )
                    WHERE favorite_list_id IS NULL;
                """)
                self.stdout.write("Updated existing favorites successfully")
            except DatabaseError as e:
                self.stdout.write(f"Error updating existing favorites: {e}")

            self.stdout.write("Creating indexes for better performance...")

            # Create indexes for better performance
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_favoritelist_user_id
                    ON favorites_favoritelist(user_id);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_favoritelist_is_default
                    ON favorites_favoritelist(is_default);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_favorite_list_id
                    ON favorites_favorite(favorite_list_id);
                """)
                self.stdout.write("Indexes created successfully")
            except DatabaseError as e:
                self.stdout.write(f"Error creating indexes: {e}")

            self.stdout.write(
                self.style.SUCCESS("Successfully created FavoriteList tables!")
            )
