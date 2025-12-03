"""Repository pattern for database operations.

Provides high-level repository interfaces for storing and retrieving historical
analyst ratings and other time-sensitive data from the SQLite database.
"""

from datetime import date, datetime
from pathlib import Path

from loguru import logger
from sqlmodel import select

from src.data.db import DatabaseManager
from src.data.models import AnalystData, AnalystRating


class AnalystRatingsRepository:
    """Repository for storing and retrieving historical analyst ratings.

    Manages CRUD operations for analyst ratings in the SQLite database,
    with additional methods for querying historical data.
    """

    def __init__(self, db_path: Path | str = "data/nordinvest.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        # Create instance-specific database manager (not global) for better test isolation
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def store_ratings(self, ratings: AnalystRating, data_source: str = "unknown") -> bool:
        """Store analyst ratings for a specific month.

        Stores monthly snapshots of ratings. Automatically converts the rating_date
        to the first day of the month for consistent period grouping.

        Args:
            ratings: AnalystRating object with rating data.
            data_source: Source of the data (e.g., 'Finnhub', 'AlphaVantage').

        Returns:
            True if successful, False otherwise.
        """
        # Normalize ticker to uppercase for consistency
        ticker = ratings.ticker.upper()

        try:
            # Extract month period (first day of month)
            period = self._get_period_start(ratings.rating_date)

            # Parse rating counts from consensus or use defaults
            strong_buy, buy, hold, sell, strong_sell = self._parse_ratings(ratings)

            # Create database record
            analyst_data = AnalystData(
                ticker=ticker,
                period=period,
                strong_buy=strong_buy,
                buy=buy,
                hold=hold,
                sell=sell,
                strong_sell=strong_sell,
                total_analysts=ratings.num_analysts or 0,
                data_source=data_source,
                fetched_at=datetime.now(),
            )

            # Store in database (upsert pattern)
            session = self.db_manager.get_session()
            try:
                # Check if record exists
                existing = session.exec(
                    select(AnalystData).where(
                        (AnalystData.ticker == analyst_data.ticker)
                        & (AnalystData.period == analyst_data.period)
                        & (AnalystData.data_source == analyst_data.data_source)
                    )
                ).first()

                if existing:
                    # Update existing record
                    existing.strong_buy = analyst_data.strong_buy
                    existing.buy = analyst_data.buy
                    existing.hold = analyst_data.hold
                    existing.sell = analyst_data.sell
                    existing.strong_sell = analyst_data.strong_sell
                    existing.total_analysts = analyst_data.total_analysts
                    existing.fetched_at = datetime.now()
                    session.add(existing)
                else:
                    # Add new record
                    session.add(analyst_data)

                session.commit()
                logger.debug(
                    f"Stored analyst ratings for {ticker} (period: {period}, source: {data_source})"
                )
                return True

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error storing analyst ratings for {ticker}: {e}")
            return False

    def get_ratings(self, ticker: str, period: date) -> AnalystRating | None:
        """Get analyst ratings for a specific ticker and period.

        Args:
            ticker: Stock ticker symbol.
            period: Period (first day of month).

        Returns:
            AnalystRating object or None if not found.
        """
        try:
            session = self.db_manager.get_session()
            try:
                analyst_data = session.exec(
                    select(AnalystData).where(
                        (AnalystData.ticker == ticker.upper()) & (AnalystData.period == period)
                    )
                ).first()

                return analyst_data.to_analyst_rating() if analyst_data else None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving analyst ratings for {ticker}: {e}")
            return None

    def get_latest_ratings(self, ticker: str) -> AnalystRating | None:
        """Get the most recent analyst ratings for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            AnalystRating object or None if not found.
        """
        try:
            session = self.db_manager.get_session()
            try:
                analyst_data = session.exec(
                    select(AnalystData)
                    .where(AnalystData.ticker == ticker.upper())
                    .order_by(AnalystData.period.desc())
                ).first()

                return analyst_data.to_analyst_rating() if analyst_data else None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving latest analyst ratings for {ticker}: {e}")
            return None

    def get_ratings_history(
        self, ticker: str, start_period: date, end_period: date
    ) -> list[AnalystRating]:
        """Get historical analyst ratings for a ticker over a date range.

        Args:
            ticker: Stock ticker symbol.
            start_period: Start period (first day of month).
            end_period: End period (first day of month).

        Returns:
            List of AnalystRating objects, sorted by period ascending.
        """
        try:
            session = self.db_manager.get_session()
            try:
                analyst_data_list = session.exec(
                    select(AnalystData)
                    .where(
                        (AnalystData.ticker == ticker.upper())
                        & (AnalystData.period >= start_period)
                        & (AnalystData.period <= end_period)
                    )
                    .order_by(AnalystData.period.asc())
                ).all()

                return [data.to_analyst_rating() for data in analyst_data_list]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving analyst ratings history for {ticker}: {e}")
            return []

    def delete_ratings(self, ticker: str, period: date) -> bool:
        """Delete analyst ratings for a specific ticker and period.

        Args:
            ticker: Stock ticker symbol.
            period: Period (first day of month).

        Returns:
            True if successful, False otherwise.
        """
        try:
            session = self.db_manager.get_session()
            try:
                analyst_data = session.exec(
                    select(AnalystData).where(
                        (AnalystData.ticker == ticker.upper()) & (AnalystData.period == period)
                    )
                ).first()

                if analyst_data:
                    session.delete(analyst_data)
                    session.commit()
                    logger.debug(f"Deleted analyst ratings for {ticker} (period: {period})")
                    return True

                logger.warning(f"No ratings found for {ticker} (period: {period})")
                return False

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error deleting analyst ratings for {ticker}: {e}")
            return False

    def get_all_tickers_with_data(self) -> list[str]:
        """Get all unique tickers in the database.

        Returns:
            List of unique tickers.
        """
        try:
            session = self.db_manager.get_session()
            try:
                tickers = session.exec(select(AnalystData.ticker).distinct()).all()
                return sorted(list(set(tickers)))

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving tickers: {e}")
            return []

    def get_data_count(self) -> int:
        """Get total number of analyst rating records in database.

        Returns:
            Total count of records.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # SQLModel doesn't have count() directly, so use func.count()
                from sqlalchemy import func

                count = session.exec(select(func.count(AnalystData.id))).one()
                return count or 0

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving data count: {e}")
            return 0

    # Helper methods

    @staticmethod
    def _get_period_start(dt: datetime | date) -> date:
        """Convert a datetime/date to the first day of its month.

        Args:
            dt: Input datetime or date.

        Returns:
            First day of the month as date object.
        """
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.replace(day=1)

    @staticmethod
    def _parse_ratings(ratings: AnalystRating) -> tuple[int, int, int, int, int]:
        """Parse rating counts from AnalystRating.

        Attempts to extract rating distribution. If not available, uses consensus
        to estimate the distribution.

        Args:
            ratings: AnalystRating object.

        Returns:
            Tuple of (strong_buy, buy, hold, sell, strong_sell) counts.
        """
        total = ratings.num_analysts or 1

        # If we only have consensus, estimate distribution
        if ratings.consensus:
            consensus = ratings.consensus.lower()
            # Simple distribution: 40% consensus, 15% each of neighbors, 10% other
            if consensus == "strong_buy":
                return (int(total * 0.4), int(total * 0.3), int(total * 0.2), 0, 0)
            elif consensus == "buy":
                return (int(total * 0.2), int(total * 0.4), int(total * 0.3), int(total * 0.1), 0)
            elif consensus == "hold":
                return (
                    int(total * 0.1),
                    int(total * 0.2),
                    int(total * 0.4),
                    int(total * 0.2),
                    int(total * 0.1),
                )
            elif consensus == "sell":
                return (0, int(total * 0.1), int(total * 0.3), int(total * 0.4), int(total * 0.2))
            elif consensus == "strong_sell":
                return (0, 0, int(total * 0.2), int(total * 0.3), int(total * 0.4))

        # Default distribution if no consensus
        return (0, int(total * 0.3), int(total * 0.4), int(total * 0.2), 0)
