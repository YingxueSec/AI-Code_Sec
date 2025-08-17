"""
Duplicate detection and deduplication system for AI Code Audit System.

This module provides comprehensive duplicate detection including:
- Content-based duplicate detection
- Semantic similarity analysis
- Cross-analysis deduplication
- Report quality improvement
"""

import hashlib
import difflib
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SimilarityMetric(Enum):
    """Similarity calculation methods."""
    EXACT_MATCH = "exact_match"
    TEXT_SIMILARITY = "text_similarity"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    STRUCTURAL_SIMILARITY = "structural_similarity"
    HASH_SIMILARITY = "hash_similarity"


class DuplicateType(Enum):
    """Types of duplicates."""
    EXACT_DUPLICATE = "exact_duplicate"
    NEAR_DUPLICATE = "near_duplicate"
    SEMANTIC_DUPLICATE = "semantic_duplicate"
    PARTIAL_DUPLICATE = "partial_duplicate"


@dataclass
class DuplicateMatch:
    """A duplicate match between two items."""
    item1_id: str
    item2_id: str
    duplicate_type: DuplicateType
    similarity_score: float
    similarity_metric: SimilarityMetric
    common_content: Optional[str] = None
    differences: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicateGroup:
    """A group of duplicate items."""
    group_id: str
    items: List[str] = field(default_factory=list)
    representative_item: Optional[str] = None
    duplicate_type: DuplicateType = DuplicateType.NEAR_DUPLICATE
    average_similarity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicateResult:
    """Result of duplicate detection."""
    total_items: int
    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)
    duplicate_matches: List[DuplicateMatch] = field(default_factory=list)
    unique_items: List[str] = field(default_factory=list)
    deduplication_stats: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duplicate_count(self) -> int:
        """Get total number of duplicate items."""
        return sum(len(group.items) for group in self.duplicate_groups)
    
    @property
    def deduplication_rate(self) -> float:
        """Get deduplication rate percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.duplicate_count / self.total_items) * 100


class DuplicateDetector:
    """Comprehensive duplicate detection and deduplication system."""
    
    def __init__(self, similarity_threshold: float = 0.8, semantic_threshold: float = 0.7):
        """Initialize duplicate detector.
        
        Args:
            similarity_threshold: Threshold for text similarity (0.0 to 1.0)
            semantic_threshold: Threshold for semantic similarity (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.semantic_threshold = semantic_threshold
        self.content_hashes: Dict[str, str] = {}
        self.item_contents: Dict[str, str] = {}
    
    def detect_duplicates(self, items: Dict[str, Any]) -> DuplicateResult:
        """Detect duplicates in a collection of items.
        
        Args:
            items: Dict mapping item IDs to item data (must have 'content' or 'analysis' field)
        """
        result = DuplicateResult(total_items=len(items))
        
        # Extract content and build hashes
        self._build_content_index(items)
        
        # Find exact duplicates first
        exact_groups = self._find_exact_duplicates()
        
        # Find near duplicates
        near_groups = self._find_near_duplicates(exact_groups)
        
        # Find semantic duplicates
        semantic_groups = self._find_semantic_duplicates(exact_groups, near_groups)
        
        # Combine all groups
        all_groups = exact_groups + near_groups + semantic_groups
        result.duplicate_groups = all_groups
        
        # Find unique items
        duplicated_items = set()
        for group in all_groups:
            duplicated_items.update(group.items)
        
        result.unique_items = [item_id for item_id in items.keys() if item_id not in duplicated_items]
        
        # Generate matches
        result.duplicate_matches = self._generate_matches(all_groups)
        
        # Calculate statistics
        result.deduplication_stats = self._calculate_stats(result, items)
        
        logger.info(f"Duplicate detection complete: {len(all_groups)} groups, {result.duplicate_count} duplicates")
        
        return result
    
    def deduplicate_analysis_results(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate analysis results and return cleaned list."""
        if not analysis_results:
            return analysis_results
        
        # Create items dict for duplicate detection
        items = {str(i): result for i, result in enumerate(analysis_results)}
        
        # Detect duplicates
        duplicate_result = self.detect_duplicates(items)
        
        # Build deduplicated list
        deduplicated = []
        processed_items = set()
        
        # Add representative items from duplicate groups
        for group in duplicate_result.duplicate_groups:
            if group.representative_item and group.representative_item not in processed_items:
                item_index = int(group.representative_item)
                deduplicated.append(analysis_results[item_index])
                processed_items.update(group.items)
        
        # Add unique items
        for item_id in duplicate_result.unique_items:
            if item_id not in processed_items:
                item_index = int(item_id)
                deduplicated.append(analysis_results[item_index])
                processed_items.add(item_id)
        
        logger.info(f"Deduplication: {len(analysis_results)} -> {len(deduplicated)} items")
        
        return deduplicated
    
    def _build_content_index(self, items: Dict[str, Any]):
        """Build content index for duplicate detection."""
        self.content_hashes.clear()
        self.item_contents.clear()
        
        for item_id, item_data in items.items():
            # Extract content
            content = ""
            if isinstance(item_data, dict):
                content = item_data.get('analysis', '') or item_data.get('content', '') or str(item_data)
            else:
                content = str(item_data)
            
            # Normalize content
            normalized_content = self._normalize_content(content)
            
            # Store content and hash
            self.item_contents[item_id] = normalized_content
            self.content_hashes[item_id] = hashlib.md5(normalized_content.encode()).hexdigest()
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison."""
        # Remove extra whitespace and normalize line endings
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return '\n'.join(lines).lower()
    
    def _find_exact_duplicates(self) -> List[DuplicateGroup]:
        """Find exact duplicate groups based on content hash."""
        hash_groups: Dict[str, List[str]] = {}
        
        for item_id, content_hash in self.content_hashes.items():
            if content_hash not in hash_groups:
                hash_groups[content_hash] = []
            hash_groups[content_hash].append(item_id)
        
        # Create groups for hashes with multiple items
        groups = []
        for content_hash, item_ids in hash_groups.items():
            if len(item_ids) > 1:
                group = DuplicateGroup(
                    group_id=f"exact_{content_hash[:8]}",
                    items=item_ids,
                    representative_item=item_ids[0],  # First item as representative
                    duplicate_type=DuplicateType.EXACT_DUPLICATE,
                    average_similarity=1.0,
                    metadata={'content_hash': content_hash}
                )
                groups.append(group)
        
        return groups
    
    def _find_near_duplicates(self, exact_groups: List[DuplicateGroup]) -> List[DuplicateGroup]:
        """Find near duplicate groups using text similarity."""
        # Get items not in exact duplicate groups
        exact_items = set()
        for group in exact_groups:
            exact_items.update(group.items)
        
        remaining_items = [item_id for item_id in self.item_contents.keys() if item_id not in exact_items]
        
        if len(remaining_items) < 2:
            return []
        
        # Find similar pairs
        similar_pairs = []
        for i, item1 in enumerate(remaining_items):
            for item2 in remaining_items[i + 1:]:
                similarity = self._calculate_text_similarity(
                    self.item_contents[item1],
                    self.item_contents[item2]
                )
                
                if similarity >= self.similarity_threshold:
                    similar_pairs.append((item1, item2, similarity))
        
        # Group similar items
        groups = self._build_similarity_groups(similar_pairs, DuplicateType.NEAR_DUPLICATE)
        
        return groups
    
    def _find_semantic_duplicates(self, exact_groups: List[DuplicateGroup], near_groups: List[DuplicateGroup]) -> List[DuplicateGroup]:
        """Find semantic duplicate groups."""
        # Get items not in existing groups
        grouped_items = set()
        for group in exact_groups + near_groups:
            grouped_items.update(group.items)
        
        remaining_items = [item_id for item_id in self.item_contents.keys() if item_id not in grouped_items]
        
        if len(remaining_items) < 2:
            return []
        
        # Find semantically similar pairs
        similar_pairs = []
        for i, item1 in enumerate(remaining_items):
            for item2 in remaining_items[i + 1:]:
                similarity = self._calculate_semantic_similarity(
                    self.item_contents[item1],
                    self.item_contents[item2]
                )
                
                if similarity >= self.semantic_threshold:
                    similar_pairs.append((item1, item2, similarity))
        
        # Group semantically similar items
        groups = self._build_similarity_groups(similar_pairs, DuplicateType.SEMANTIC_DUPLICATE)
        
        return groups
    
    def _build_similarity_groups(self, similar_pairs: List[Tuple[str, str, float]], duplicate_type: DuplicateType) -> List[DuplicateGroup]:
        """Build groups from similarity pairs."""
        if not similar_pairs:
            return []
        
        # Build adjacency list
        adjacency: Dict[str, Set[str]] = {}
        similarities: Dict[Tuple[str, str], float] = {}
        
        for item1, item2, similarity in similar_pairs:
            if item1 not in adjacency:
                adjacency[item1] = set()
            if item2 not in adjacency:
                adjacency[item2] = set()
            
            adjacency[item1].add(item2)
            adjacency[item2].add(item1)
            similarities[(item1, item2)] = similarity
            similarities[(item2, item1)] = similarity
        
        # Find connected components
        visited = set()
        groups = []
        
        for item in adjacency:
            if item not in visited:
                component = self._find_connected_component(item, adjacency, visited)
                if len(component) > 1:
                    # Calculate average similarity
                    total_similarity = 0.0
                    pair_count = 0
                    
                    for i, item1 in enumerate(component):
                        for item2 in component[i + 1:]:
                            key = (item1, item2) if (item1, item2) in similarities else (item2, item1)
                            if key in similarities:
                                total_similarity += similarities[key]
                                pair_count += 1
                    
                    avg_similarity = total_similarity / pair_count if pair_count > 0 else 0.0
                    
                    # Choose representative (item with highest average similarity to others)
                    representative = self._choose_representative(component, similarities)
                    
                    group = DuplicateGroup(
                        group_id=f"{duplicate_type.value}_{len(groups)}",
                        items=component,
                        representative_item=representative,
                        duplicate_type=duplicate_type,
                        average_similarity=avg_similarity
                    )
                    groups.append(group)
        
        return groups
    
    def _find_connected_component(self, start_item: str, adjacency: Dict[str, Set[str]], visited: Set[str]) -> List[str]:
        """Find connected component using DFS."""
        component = []
        stack = [start_item]
        
        while stack:
            item = stack.pop()
            if item not in visited:
                visited.add(item)
                component.append(item)
                
                for neighbor in adjacency.get(item, set()):
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        return component
    
    def _choose_representative(self, items: List[str], similarities: Dict[Tuple[str, str], float]) -> str:
        """Choose representative item from a group."""
        if len(items) == 1:
            return items[0]
        
        # Calculate average similarity for each item
        item_scores = {}
        
        for item in items:
            total_similarity = 0.0
            count = 0
            
            for other_item in items:
                if item != other_item:
                    key = (item, other_item) if (item, other_item) in similarities else (other_item, item)
                    if key in similarities:
                        total_similarity += similarities[key]
                        count += 1
            
            item_scores[item] = total_similarity / count if count > 0 else 0.0
        
        # Return item with highest average similarity
        return max(item_scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using difflib."""
        if not text1 or not text2:
            return 0.0
        
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity (simplified implementation)."""
        if not text1 or not text2:
            return 0.0
        
        # Extract key terms and concepts
        terms1 = self._extract_key_terms(text1)
        terms2 = self._extract_key_terms(text2)
        
        if not terms1 or not terms2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(terms1.intersection(terms2))
        union = len(terms1.union(terms2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_key_terms(self, text: str) -> Set[str]:
        """Extract key terms from text for semantic comparison."""
        import re
        
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Extract words and filter
        words = re.findall(r'\b\w+\b', text.lower())
        key_terms = set()
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                key_terms.add(word)
        
        return key_terms
    
    def _generate_matches(self, groups: List[DuplicateGroup]) -> List[DuplicateMatch]:
        """Generate duplicate matches from groups."""
        matches = []
        
        for group in groups:
            # Generate pairwise matches within group
            for i, item1 in enumerate(group.items):
                for item2 in group.items[i + 1:]:
                    # Calculate similarity between the pair
                    similarity = self._calculate_text_similarity(
                        self.item_contents[item1],
                        self.item_contents[item2]
                    )
                    
                    match = DuplicateMatch(
                        item1_id=item1,
                        item2_id=item2,
                        duplicate_type=group.duplicate_type,
                        similarity_score=similarity,
                        similarity_metric=SimilarityMetric.TEXT_SIMILARITY,
                        metadata={'group_id': group.group_id}
                    )
                    matches.append(match)
        
        return matches
    
    def _calculate_stats(self, result: DuplicateResult, original_items: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate deduplication statistics."""
        stats = {
            'original_count': len(original_items),
            'duplicate_groups': len(result.duplicate_groups),
            'total_duplicates': result.duplicate_count,
            'unique_items': len(result.unique_items),
            'deduplication_rate': result.deduplication_rate,
            'space_saved_percentage': (result.duplicate_count / len(original_items) * 100) if original_items else 0,
        }
        
        # Group statistics by type
        type_stats = {}
        for group in result.duplicate_groups:
            group_type = group.duplicate_type.value
            if group_type not in type_stats:
                type_stats[group_type] = {'groups': 0, 'items': 0}
            
            type_stats[group_type]['groups'] += 1
            type_stats[group_type]['items'] += len(group.items)
        
        stats['by_type'] = type_stats
        
        return stats
