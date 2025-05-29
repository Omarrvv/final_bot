"""
Query Analyzer for the Egypt Tourism Chatbot.

This module provides tools for analyzing and optimizing database queries.
"""
import time
import logging
import statistics
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """
    Query analyzer for identifying and optimizing slow queries.
    
    This class provides tools for tracking query performance, analyzing query plans,
    and suggesting optimizations.
    """
    
    def __init__(self, slow_query_threshold_ms: int = 500, max_queries_to_track: int = 100):
        """
        Initialize the query analyzer.
        
        Args:
            slow_query_threshold_ms: Threshold in milliseconds for identifying slow queries
            max_queries_to_track: Maximum number of queries to track
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.max_queries_to_track = max_queries_to_track
        self.query_stats = defaultdict(list)
        self.slow_queries = []
        self.query_plans = {}
    
    def record_query(self, query: str, params: Tuple, duration_ms: float, rows_affected: int) -> None:
        """
        Record a query execution for analysis.
        
        Args:
            query: SQL query string
            params: Query parameters
            duration_ms: Execution time in milliseconds
            rows_affected: Number of rows affected or returned
        """
        # Normalize the query by removing extra whitespace
        normalized_query = ' '.join(query.strip().split())
        
        # Record query stats
        self.query_stats[normalized_query].append({
            'duration_ms': duration_ms,
            'rows_affected': rows_affected,
            'timestamp': time.time(),
            'params': params
        })
        
        # Trim the stats if needed
        if len(self.query_stats[normalized_query]) > self.max_queries_to_track:
            self.query_stats[normalized_query] = self.query_stats[normalized_query][-self.max_queries_to_track:]
        
        # Record slow queries
        if duration_ms > self.slow_query_threshold_ms:
            self.slow_queries.append({
                'query': normalized_query,
                'params': params,
                'duration_ms': duration_ms,
                'rows_affected': rows_affected,
                'timestamp': time.time()
            })
            
            # Trim the slow queries list if needed
            if len(self.slow_queries) > self.max_queries_to_track:
                self.slow_queries = self.slow_queries[-self.max_queries_to_track:]
            
            logger.warning(f"Slow query detected ({duration_ms:.2f}ms): {normalized_query}")
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Get the list of slow queries.
        
        Returns:
            List of slow queries with their stats
        """
        return sorted(self.slow_queries, key=lambda q: q['duration_ms'], reverse=True)
    
    def get_query_stats(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for queries.
        
        Args:
            query: Optional specific query to get stats for
            
        Returns:
            Dictionary of query statistics
        """
        if query:
            normalized_query = ' '.join(query.strip().split())
            stats = self.query_stats.get(normalized_query, [])
            if not stats:
                return {}
            
            durations = [s['duration_ms'] for s in stats]
            rows = [s['rows_affected'] for s in stats]
            
            return {
                'count': len(stats),
                'avg_duration_ms': statistics.mean(durations) if durations else 0,
                'min_duration_ms': min(durations) if durations else 0,
                'max_duration_ms': max(durations) if durations else 0,
                'median_duration_ms': statistics.median(durations) if durations else 0,
                'p95_duration_ms': statistics.quantiles(durations, n=20)[19] if len(durations) >= 20 else max(durations) if durations else 0,
                'avg_rows': statistics.mean(rows) if rows else 0,
                'total_rows': sum(rows),
                'last_executed': max(s['timestamp'] for s in stats) if stats else None
            }
        else:
            result = {}
            for q, stats in self.query_stats.items():
                if not stats:
                    continue
                
                durations = [s['duration_ms'] for s in stats]
                rows = [s['rows_affected'] for s in stats]
                
                result[q] = {
                    'count': len(stats),
                    'avg_duration_ms': statistics.mean(durations) if durations else 0,
                    'min_duration_ms': min(durations) if durations else 0,
                    'max_duration_ms': max(durations) if durations else 0,
                    'median_duration_ms': statistics.median(durations) if durations else 0,
                    'p95_duration_ms': statistics.quantiles(durations, n=20)[19] if len(durations) >= 20 else max(durations) if durations else 0,
                    'avg_rows': statistics.mean(rows) if rows else 0,
                    'total_rows': sum(rows),
                    'last_executed': max(s['timestamp'] for s in stats) if stats else None
                }
            
            return result
    
    def analyze_query_plan(self, db_manager, query: str, params: Tuple) -> Dict[str, Any]:
        """
        Analyze the execution plan for a query.
        
        Args:
            db_manager: Database manager instance
            query: SQL query string
            params: Query parameters
            
        Returns:
            Dictionary containing the query plan and analysis
        """
        normalized_query = ' '.join(query.strip().split())
        
        # Check if we already have a plan for this query
        if normalized_query in self.query_plans:
            return self.query_plans[normalized_query]
        
        try:
            # Get the query plan using EXPLAIN ANALYZE
            explain_query = f"EXPLAIN (ANALYZE, VERBOSE, BUFFERS, FORMAT JSON) {query}"
            result = db_manager.execute_postgres_query(explain_query, params, fetchall=False)
            
            if not result or not isinstance(result, dict) or 'QUERY PLAN' not in result:
                logger.warning(f"Failed to get query plan for: {normalized_query}")
                return {}
            
            plan = result['QUERY PLAN']
            
            # Extract key information from the plan
            analysis = self._analyze_plan(plan)
            
            # Store the plan and analysis
            self.query_plans[normalized_query] = {
                'plan': plan,
                'analysis': analysis
            }
            
            return self.query_plans[normalized_query]
        except Exception as e:
            logger.error(f"Error analyzing query plan: {str(e)}")
            return {}
    
    def _analyze_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a query plan to identify optimization opportunities.
        
        Args:
            plan: Query plan from EXPLAIN ANALYZE
            
        Returns:
            Dictionary containing analysis and recommendations
        """
        if not plan or not isinstance(plan, list) or not plan[0]:
            return {}
        
        plan_data = plan[0]
        
        # Extract the root node of the plan
        root_node = plan_data.get('Plan', {})
        
        # Initialize analysis
        analysis = {
            'execution_time_ms': 0,
            'planning_time_ms': 0,
            'total_cost': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Extract execution and planning time
        if 'Execution Time' in plan_data:
            analysis['execution_time_ms'] = plan_data['Execution Time']
        
        if 'Planning Time' in plan_data:
            analysis['planning_time_ms'] = plan_data['Planning Time']
        
        # Extract total cost
        if 'Total Cost' in root_node:
            analysis['total_cost'] = root_node['Total Cost']
        
        # Analyze the plan nodes recursively
        self._analyze_plan_node(root_node, analysis)
        
        return analysis
    
    def _analyze_plan_node(self, node: Dict[str, Any], analysis: Dict[str, Any], depth: int = 0) -> None:
        """
        Recursively analyze a plan node to identify issues.
        
        Args:
            node: Plan node
            analysis: Analysis dictionary to update
            depth: Current depth in the plan tree
        """
        if not node:
            return
        
        node_type = node.get('Node Type')
        
        # Check for sequential scans on large tables
        if node_type == 'Seq Scan' and node.get('Relation Name') and node.get('Plan Rows', 0) > 1000:
            table_name = node.get('Relation Name')
            analysis['issues'].append(f"Sequential scan on potentially large table: {table_name}")
            analysis['recommendations'].append(f"Consider adding an index on {table_name} for the columns used in the WHERE clause")
        
        # Check for hash joins with high costs
        if node_type == 'Hash Join' and node.get('Total Cost', 0) > 1000:
            analysis['issues'].append("Expensive hash join operation")
            analysis['recommendations'].append("Review join conditions and consider adding indexes on join columns")
        
        # Check for nested loops with many iterations
        if node_type == 'Nested Loop' and node.get('Plan Rows', 0) > 1000:
            analysis['issues'].append("Nested loop with many iterations")
            analysis['recommendations'].append("Consider using a different join type or adding indexes on join columns")
        
        # Check for filter conditions with low selectivity
        if 'Filter' in node and node.get('Rows Removed by Filter', 0) > 1000:
            filter_cond = node.get('Filter')
            analysis['issues'].append(f"Filter with low selectivity: {filter_cond}")
            analysis['recommendations'].append("Review filter conditions and consider adding indexes for frequently filtered columns")
        
        # Recursively analyze child nodes
        for child_key in ['Plans', 'Plan']:
            if child_key in node and isinstance(node[child_key], list):
                for child_node in node[child_key]:
                    self._analyze_plan_node(child_node, analysis, depth + 1)
            elif child_key in node and isinstance(node[child_key], dict):
                self._analyze_plan_node(node[child_key], analysis, depth + 1)
    
    def suggest_indexes(self, db_manager) -> Dict[str, List[str]]:
        """
        Suggest indexes based on query patterns.
        
        Args:
            db_manager: Database manager instance
            
        Returns:
            Dictionary mapping table names to suggested indexes
        """
        suggestions = defaultdict(list)
        
        # Analyze slow queries for potential index opportunities
        for query_info in self.slow_queries:
            query = query_info['query']
            
            # Skip queries that are not SELECT statements
            if not query.strip().upper().startswith('SELECT'):
                continue
            
            # Get the query plan
            plan_info = self.analyze_query_plan(db_manager, query, query_info['params'])
            
            if not plan_info or 'plan' not in plan_info:
                continue
            
            # Extract tables and columns from the plan
            tables_columns = self._extract_tables_columns_from_plan(plan_info['plan'])
            
            # Generate index suggestions
            for table, columns in tables_columns.items():
                if columns:
                    # Suggest single-column indexes for frequently filtered columns
                    for col in columns:
                        index_suggestion = f"CREATE INDEX idx_{table}_{col} ON {table} ({col})"
                        if index_suggestion not in suggestions[table]:
                            suggestions[table].append(index_suggestion)
                    
                    # Suggest multi-column indexes for combinations of columns
                    if len(columns) > 1:
                        cols_str = ', '.join(columns)
                        index_suggestion = f"CREATE INDEX idx_{table}_{'_'.join(columns)} ON {table} ({cols_str})"
                        if index_suggestion not in suggestions[table]:
                            suggestions[table].append(index_suggestion)
        
        return dict(suggestions)
    
    def _extract_tables_columns_from_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract tables and columns from a query plan.
        
        Args:
            plan: Query plan from EXPLAIN ANALYZE
            
        Returns:
            Dictionary mapping table names to lists of columns
        """
        tables_columns = defaultdict(list)
        
        if not plan or not isinstance(plan, list) or not plan[0]:
            return tables_columns
        
        plan_data = plan[0]
        root_node = plan_data.get('Plan', {})
        
        # Extract tables and columns recursively
        self._extract_tables_columns_from_node(root_node, tables_columns)
        
        return tables_columns
    
    def _extract_tables_columns_from_node(self, node: Dict[str, Any], tables_columns: Dict[str, List[str]]) -> None:
        """
        Recursively extract tables and columns from a plan node.
        
        Args:
            node: Plan node
            tables_columns: Dictionary to update with tables and columns
        """
        if not node:
            return
        
        # Extract table name
        table_name = node.get('Relation Name')
        
        # Extract columns from various node properties
        if table_name:
            # Extract columns from Index Cond
            if 'Index Cond' in node:
                cond = node['Index Cond']
                columns = self._extract_columns_from_condition(cond)
                for col in columns:
                    if col not in tables_columns[table_name]:
                        tables_columns[table_name].append(col)
            
            # Extract columns from Filter
            if 'Filter' in node:
                cond = node['Filter']
                columns = self._extract_columns_from_condition(cond)
                for col in columns:
                    if col not in tables_columns[table_name]:
                        tables_columns[table_name].append(col)
            
            # Extract columns from Recheck Cond
            if 'Recheck Cond' in node:
                cond = node['Recheck Cond']
                columns = self._extract_columns_from_condition(cond)
                for col in columns:
                    if col not in tables_columns[table_name]:
                        tables_columns[table_name].append(col)
        
        # Recursively extract from child nodes
        for child_key in ['Plans', 'Plan']:
            if child_key in node and isinstance(node[child_key], list):
                for child_node in node[child_key]:
                    self._extract_tables_columns_from_node(child_node, tables_columns)
            elif child_key in node and isinstance(node[child_key], dict):
                self._extract_tables_columns_from_node(node[child_key], tables_columns)
    
    def _extract_columns_from_condition(self, condition: str) -> List[str]:
        """
        Extract column names from a condition string.
        
        Args:
            condition: Condition string from query plan
            
        Returns:
            List of column names
        """
        columns = []
        
        if not condition or not isinstance(condition, str):
            return columns
        
        # Simple parsing of conditions like "table.column = value"
        parts = condition.split()
        for part in parts:
            if '.' in part:
                # Extract column name from "table.column"
                table_col = part.split('.')
                if len(table_col) == 2:
                    col = table_col[1].strip('()"\'')
                    if col and col not in columns:
                        columns.append(col)
            elif part and part[0].isalpha() and part not in ['AND', 'OR', 'NOT', 'IN', 'IS', 'NULL']:
                # Assume it's a column name if it starts with a letter and is not a SQL keyword
                col = part.strip('()"\'')
                if col and col not in columns:
                    columns.append(col)
        
        return columns
