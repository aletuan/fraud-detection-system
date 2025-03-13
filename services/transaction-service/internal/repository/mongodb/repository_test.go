package mongodb

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"transaction-service/internal/domain"
	"transaction-service/internal/repository"
)

func setupTestDB(t *testing.T) (*mongo.Database, func()) {
	ctx := context.Background()
	client, err := mongo.Connect(ctx, options.Client().ApplyURI("mongodb://localhost:27017"))
	require.NoError(t, err)

	dbName := "test_db_" + primitive.NewObjectID().Hex()
	db := client.Database(dbName)

	return db, func() {
		err := db.Drop(ctx)
		require.NoError(t, err)
		err = client.Disconnect(ctx)
		require.NoError(t, err)
	}
}

func cleanupCollection(collection *mongo.Collection) error {
	_, err := collection.DeleteMany(context.Background(), bson.M{})
	return err
}

func TestMongoRepository(t *testing.T) {
	db, cleanup := setupTestDB(t)
	defer cleanup()

	repo := NewMongoRepository(db).(*mongoRepository)
	ctx := context.Background()

	t.Run("Create and GetByID", func(t *testing.T) {
		require.NoError(t, cleanupCollection(repo.collection))

		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      100.50,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF-" + primitive.NewObjectID().Hex(),
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		err := repo.Create(ctx, tx)
		require.NoError(t, err)

		found, err := repo.GetByID(ctx, tx.ID.Hex())
		require.NoError(t, err)
		assert.Equal(t, tx.ID, found.ID)
		assert.Equal(t, tx.AccountID, found.AccountID)
		assert.Equal(t, tx.Amount, found.Amount)
	})

	t.Run("Update", func(t *testing.T) {
		require.NoError(t, cleanupCollection(repo.collection))

		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      100.50,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF-" + primitive.NewObjectID().Hex(),
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		err := repo.Create(ctx, tx)
		require.NoError(t, err)

		tx.Amount = 200.50
		tx.Status = domain.StatusCompleted

		err = repo.Update(ctx, tx)
		require.NoError(t, err)

		found, err := repo.GetByID(ctx, tx.ID.Hex())
		require.NoError(t, err)
		assert.Equal(t, 200.50, found.Amount)
		assert.Equal(t, domain.StatusCompleted, found.Status)
	})

	t.Run("Delete", func(t *testing.T) {
		require.NoError(t, cleanupCollection(repo.collection))

		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      100.50,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF-" + primitive.NewObjectID().Hex(),
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		err := repo.Create(ctx, tx)
		require.NoError(t, err)

		err = repo.Delete(ctx, tx.ID.Hex())
		require.NoError(t, err)

		_, err = repo.GetByID(ctx, tx.ID.Hex())
		assert.Equal(t, repository.ErrNotFound, err)
	})

	t.Run("List with Pagination", func(t *testing.T) {
		require.NoError(t, cleanupCollection(repo.collection))

		// Create 15 transactions
		for i := 0; i < 15; i++ {
			tx := &domain.Transaction{
				ID:          primitive.NewObjectID(),
				AccountID:   "acc123",
				Amount:      100.50,
				Currency:    "USD",
				Type:        domain.TransactionTypeDebit,
				Status:      domain.StatusPending,
				ReferenceID: "REF-" + primitive.NewObjectID().Hex(),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			}
			err := repo.Create(ctx, tx)
			require.NoError(t, err)
		}

		params := repository.ListParams{
			Page:     1,
			PageSize: 10,
			SortBy:   "created_at",
			SortDesc: true,
		}

		transactions, total, err := repo.List(ctx, params)
		require.NoError(t, err)
		assert.Equal(t, 10, len(transactions))
		assert.Equal(t, int64(15), total)
	})

	t.Run("GetByAccountID", func(t *testing.T) {
		require.NoError(t, cleanupCollection(repo.collection))

		// Create transactions for different accounts
		accounts := []string{"acc1", "acc2", "acc3"}
		for _, acc := range accounts {
			for i := 0; i < 5; i++ {
				tx := &domain.Transaction{
					ID:          primitive.NewObjectID(),
					AccountID:   acc,
					Amount:      100.50,
					Currency:    "USD",
					Type:        domain.TransactionTypeDebit,
					Status:      domain.StatusPending,
					ReferenceID: "REF-" + primitive.NewObjectID().Hex(),
					CreatedAt:   time.Now(),
					UpdatedAt:   time.Now(),
				}
				err := repo.Create(ctx, tx)
				require.NoError(t, err)
			}
		}

		params := repository.NewListParams()
		transactions, total, err := repo.GetByAccountID(ctx, "acc1", params)
		require.NoError(t, err)
		assert.Equal(t, 5, len(transactions))
		assert.Equal(t, int64(5), total)
	})
} 