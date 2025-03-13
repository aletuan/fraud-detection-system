package mongodb

import (
	"context"
	"strings"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"transaction-service/internal/domain"
	"transaction-service/internal/repository"
)

type mongoRepository struct {
	collection *mongo.Collection
}

// NewMongoRepository creates a new MongoDB repository
func NewMongoRepository(db *mongo.Database) repository.TransactionRepository {
	// Create collection if it doesn't exist
	collectionName := "transactions"
	err := db.CreateCollection(context.Background(), collectionName)
	if err != nil {
		// Ignore error if collection already exists
		if !strings.Contains(err.Error(), "already exists") {
			panic(err)
		}
	}

	collection := db.Collection(collectionName)
	
	// Create indexes
	indexes := []mongo.IndexModel{
		{
			Keys: bson.D{
				{Key: "reference_id", Value: 1},
			},
			Options: options.Index().SetUnique(true),
		},
		{
			Keys: bson.D{
				{Key: "account_id", Value: 1},
				{Key: "created_at", Value: -1},
			},
		},
		{
			Keys: bson.D{
				{Key: "created_at", Value: 1},
			},
		},
	}

	_, err = collection.Indexes().CreateMany(context.Background(), indexes)
	if err != nil {
		panic(err) // In production, handle this error appropriately
	}

	return &mongoRepository{
		collection: collection,
	}
}

func (r *mongoRepository) Create(ctx context.Context, tx *domain.Transaction) error {
	if tx.ID.IsZero() {
		tx.ID = primitive.NewObjectID()
	}
	
	tx.CreatedAt = time.Now()
	tx.UpdatedAt = tx.CreatedAt

	_, err := r.collection.InsertOne(ctx, tx)
	if mongo.IsDuplicateKeyError(err) {
		return repository.ErrDuplicateKey
	}
	return err
}

func (r *mongoRepository) GetByID(ctx context.Context, id string) (*domain.Transaction, error) {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return nil, repository.ErrInvalidID
	}

	var transaction domain.Transaction
	err = r.collection.FindOne(ctx, bson.M{"_id": objectID}).Decode(&transaction)
	if err == mongo.ErrNoDocuments {
		return nil, repository.ErrNotFound
	}
	return &transaction, err
}

func (r *mongoRepository) Update(ctx context.Context, tx *domain.Transaction) error {
	tx.UpdatedAt = time.Now()

	result, err := r.collection.ReplaceOne(
		ctx,
		bson.M{"_id": tx.ID},
		tx,
	)
	if err != nil {
		return err
	}
	if result.MatchedCount == 0 {
		return repository.ErrNotFound
	}
	return nil
}

func (r *mongoRepository) Delete(ctx context.Context, id string) error {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return repository.ErrInvalidID
	}

	result, err := r.collection.DeleteOne(ctx, bson.M{"_id": objectID})
	if err != nil {
		return err
	}
	if result.DeletedCount == 0 {
		return repository.ErrNotFound
	}
	return nil
}

func (r *mongoRepository) List(ctx context.Context, params repository.ListParams) ([]domain.Transaction, int64, error) {
	filter := bson.M{}
	for key, value := range params.Filters {
		filter[key] = value
	}

	// Calculate skip value for pagination
	skip := (params.Page - 1) * params.PageSize

	// Set up sort order
	sortOrder := 1
	if params.SortDesc {
		sortOrder = -1
	}

	findOptions := options.Find().
		SetSort(bson.D{{Key: params.SortBy, Value: sortOrder}}).
		SetSkip(int64(skip)).
		SetLimit(int64(params.PageSize))

	// Get total count
	total, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return nil, 0, err
	}

	// Get transactions
	cursor, err := r.collection.Find(ctx, filter, findOptions)
	if err != nil {
		return nil, 0, err
	}
	defer cursor.Close(ctx)

	var transactions []domain.Transaction
	if err = cursor.All(ctx, &transactions); err != nil {
		return nil, 0, err
	}

	return transactions, total, nil
}

func (r *mongoRepository) GetByReferenceID(ctx context.Context, referenceID string) (*domain.Transaction, error) {
	var transaction domain.Transaction
	err := r.collection.FindOne(ctx, bson.M{"reference_id": referenceID}).Decode(&transaction)
	if err == mongo.ErrNoDocuments {
		return nil, repository.ErrNotFound
	}
	return &transaction, err
}

func (r *mongoRepository) GetByAccountID(ctx context.Context, accountID string, params repository.ListParams) ([]domain.Transaction, int64, error) {
	params.Filters["account_id"] = accountID
	return r.List(ctx, params)
} 