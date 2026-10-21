"""Keep the GPU reservation across the one final fit and first independent review."""
import train
import review

if __name__ == '__main__':
    train.main()
    review.main()
