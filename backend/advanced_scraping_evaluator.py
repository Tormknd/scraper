#!/usr/bin/env python3

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

from scraper import analyze_website, extract_data_with_requirements, create_conversation_session
from advanced_scraper import AdvancedScraper

@dataclass
class AdvancedEvaluationResult:
    url: str
    website_type: str
    scraping_method: str
    content_length: int
    content_quality: str
    structured_data_count: int
    images_found: int
    links_found: int
    pages_scraped: int
    extraction_success: bool
    items_extracted: int
    extraction_accuracy: float
    performance_score: float
    issues: List[str]
    recommendations: List[str]

def evaluate_advanced_scraping_quality(scraped_content) -> Dict[str, Any]:
    content_length = len(scraped_content.main_content)
    
    content_quality = "high"
    if content_length < 1000:
        content_quality = "low"
    elif content_length < 5000:
        content_quality = "medium"
    
    structured_data = scraped_content.structured_data
    structured_data_count = sum(len(v) if isinstance(v, list) else 1 for v in structured_data.values())
    images_found = len(scraped_content.images)
    links_found = len(scraped_content.links)
    pages_scraped = 1
    
    content_score = min(content_length / 1000, 10)
    structure_score = min(structured_data_count * 2, 10)
    media_score = min(images_found * 0.5, 5)
    navigation_score = min(links_found * 0.1, 5)
    pages_score = min(pages_scraped * 2, 10)
    
    quality_score = content_score + structure_score + media_score + navigation_score + pages_score
    
    return {
        'content_length': content_length,
        'content_quality': content_quality,
        'structured_data_count': structured_data_count,
        'images_found': images_found,
        'links_found': links_found,
        'pages_scraped': pages_scraped,
        'quality_score': quality_score
    }

def evaluate_advanced_extraction_quality(extraction_result: Dict[str, Any], expected_items: int) -> Dict[str, Any]:
    items = extraction_result.get('items', [])
    items_extracted = len(items)
    
    extraction_accuracy = 0.0
    if expected_items > 0:
        extraction_accuracy = min(items_extracted / expected_items, 1.0)
    
    issues = []
    recommendations = []
    
    if items_extracted == 0:
        issues.append("No items extracted")
        recommendations.append("Check if the website has the requested content")
    
    if extraction_accuracy < 0.5:
        issues.append("Low extraction accuracy")
        recommendations.append("Improve extraction requirements or scraping method")
    
    for item in items:
        if not item.get('title'):
            issues.append("Items missing titles")
            break
    
    if len(items) > 0 and len(set(item.get('title', '') for item in items)) < len(items):
        issues.append("Duplicate items detected")
        recommendations.append("Implement better deduplication")
    
    quality_score = min(items_extracted * 2, 10)
    
    if not issues:
        quality_score += 5
    
    performance_score = (extraction_accuracy * 100) + (quality_score * 2)
    
    return {
        'success': items_extracted > 0,
        'items_extracted': items_extracted,
        'extraction_accuracy': extraction_accuracy,
        'quality_score': quality_score,
        'performance_score': performance_score,
        'ai_response_length': len(extraction_result.get('ai_response', '')),
        'issues': issues
    }

def test_advanced_website(url: str, website_type: str, requirements: str, expected_items: int, challenge: str) -> AdvancedEvaluationResult:
    session_id = f"advanced_eval_{int(time.time())}"
    create_conversation_session(session_id)
    
    try:
        analysis_result = analyze_website(session_id, url)
        
        if not analysis_result['success']:
            return AdvancedEvaluationResult(
                url=url,
                website_type=website_type,
                scraping_method="failed",
                content_length=0,
                content_quality="low",
                structured_data_count=0,
                images_found=0,
                links_found=0,
                pages_scraped=0,
                extraction_success=False,
                items_extracted=0,
                extraction_accuracy=0.0,
                performance_score=0.0,
                issues=["Analysis failed"],
                recommendations=["Check URL accessibility"]
            )
        
        scraper = AdvancedScraper()
        scraped_content = scraper.scrape_advanced(url, use_js=True, max_pages=3)
        
        scraping_eval = evaluate_advanced_scraping_quality(scraped_content)
        
        extraction_result = extract_data_with_requirements(session_id, requirements)
        
        extraction_eval = evaluate_advanced_extraction_quality(extraction_result.get('data', {}), expected_items)
        
        issues = []
        recommendations = []
        
        if scraping_eval['quality_score'] < 20:
            issues.append("Low content quality")
            recommendations.append("Consider using more advanced scraping methods")
        
        if extraction_eval['extraction_accuracy'] < 0.5:
            issues.append("Low extraction accuracy")
            recommendations.append("Review extraction requirements and scraping method")
        
        issues.extend(extraction_eval['issues'])
        recommendations.extend(extraction_eval['recommendations'])
        
        return AdvancedEvaluationResult(
            url=url,
            website_type=website_type,
            scraping_method="advanced",
            content_length=scraping_eval['content_length'],
            content_quality=scraping_eval['content_quality'],
            structured_data_count=scraping_eval['structured_data_count'],
            images_found=scraping_eval['images_found'],
            links_found=scraping_eval['links_found'],
            pages_scraped=scraping_eval['pages_scraped'],
            extraction_success=extraction_eval['success'],
            items_extracted=extraction_eval['items_extracted'],
            extraction_accuracy=extraction_eval['extraction_accuracy'],
            performance_score=extraction_eval['performance_score'],
            issues=issues,
            recommendations=recommendations
        )
        
    except Exception as e:
        return AdvancedEvaluationResult(
            url=url,
            website_type=website_type,
            scraping_method="error",
            content_length=0,
            content_quality="low",
            structured_data_count=0,
            images_found=0,
            links_found=0,
            pages_scraped=0,
            extraction_success=False,
            items_extracted=0,
            extraction_accuracy=0.0,
            performance_score=0.0,
            issues=[f"Error: {str(e)}"],
            recommendations=["Check system configuration"]
        )

class AdvancedScrapingEvaluator:
    def __init__(self):
        self.test_urls = [
            ("https://www.amazon.com", "ecommerce", "Extract all products with titles, prices, ratings, and images", 20, "Dynamic content with infinite scroll"),
            ("https://www.lemonde.fr", "news", "Extract all articles with titles, dates, authors, and summaries", 15, "Complex article layout with ads"),
            ("https://www.github.com", "platform", "Extract trending repositories with names, descriptions, stars, and languages", 10, "JavaScript-heavy interface"),
            ("https://www.medium.com", "blog", "Extract articles with titles, authors, reading times, and claps", 12, "Infinite scroll with dynamic loading"),
            ("https://www.reddit.com", "social", "Extract posts with titles, scores, comments, and subreddits", 25, "Complex nested content structure")
        ]
    
    def run_advanced_evaluation(self) -> Dict[str, Any]:
        results = []
        
        for url, website_type, requirements, expected_items, challenge in self.test_urls:
            time.sleep(3)
            result = test_advanced_website(url, website_type, requirements, expected_items, challenge)
            results.append(result)
        
        total_tests = len(results)
        successful_scrapes = sum(1 for r in results if r.content_length > 0)
        successful_extractions = sum(1 for r in results if r.extraction_success)
        advanced_scrapes = sum(1 for r in results if r.scraping_method == "advanced")
        avg_performance = sum(r.performance_score for r in results) / total_tests if total_tests > 0 else 0
        
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues)
            all_recommendations.extend(result.recommendations)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        performance_levels = []
        for result in results:
            if result.performance_score >= 80:
                performance_levels.append("Excellent")
            elif result.performance_score >= 60:
                performance_levels.append("Good")
            elif result.performance_score >= 40:
                performance_levels.append("Fair")
            else:
                performance_levels.append("Poor")
        
        report = {
            "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "successful_scrapes": successful_scrapes,
            "successful_extractions": successful_extractions,
            "advanced_scrapes": advanced_scrapes,
            "average_performance": avg_performance,
            "performance_levels": performance_levels,
            "results": [
                {
                    "url": r.url,
                    "website_type": r.website_type,
                    "scraping_method": r.scraping_method,
                    "content_length": r.content_length,
                    "content_quality": r.content_quality,
                    "structured_data_count": r.structured_data_count,
                    "images_found": r.images_found,
                    "links_found": r.links_found,
                    "pages_scraped": r.pages_scraped,
                    "extraction_success": r.extraction_success,
                    "items_extracted": r.items_extracted,
                    "extraction_accuracy": r.extraction_accuracy,
                    "performance_score": r.performance_score,
                    "issues": r.issues,
                    "recommendations": r.recommendations
                }
                for r in results
            ],
            "common_issues": issue_counts,
            "recommendations": recommendation_counts
        }
        
        report_path = Path("advanced_scraping_evaluation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report

if __name__ == "__main__":
    evaluator = AdvancedScrapingEvaluator()
    report = evaluator.run_advanced_evaluation() 