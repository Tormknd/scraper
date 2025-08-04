#!/usr/bin/env python3

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

from scraper import analyze_website, extract_data_with_requirements, create_conversation_session

@dataclass
class EvaluationResult:
    url: str
    website_type: str
    scraping_method: str
    content_length: int
    structured_data_count: int
    images_found: int
    links_found: int
    pages_scraped: int
    extraction_success: bool
    items_extracted: int
    issues: List[str]
    recommendations: List[str]

def evaluate_scraping_quality(scraped_data: Dict[str, Any]) -> Dict[str, Any]:
    main_page = scraped_data.get('main_page', {})
    
    content_length = len(main_page.get('content', ''))
    structured_data = main_page.get('structured_data', {})
    structured_data_count = sum(len(v) if isinstance(v, list) else 1 for v in structured_data.values())
    images_found = len(main_page.get('images', []))
    links_found = len(main_page.get('links', []))
    pages_scraped = scraped_data.get('total_pages_scraped', 1)
    
    content_score = min(content_length / 1000, 10)
    structure_score = min(structured_data_count * 2, 10)
    media_score = min(images_found * 0.5, 5)
    navigation_score = min(links_found * 0.1, 5)
    pages_score = min(pages_scraped * 2, 10)
    
    quality_score = content_score + structure_score + media_score + navigation_score + pages_score
    
    return {
        'content_length': content_length,
        'structured_data_count': structured_data_count,
        'images_found': images_found,
        'links_found': links_found,
        'pages_scraped': pages_scraped,
        'quality_score': quality_score
    }

def evaluate_extraction_quality(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    items = extraction_result.get('items', [])
    items_extracted = len(items)
    
    issues = []
    recommendations = []
    
    if items_extracted == 0:
        issues.append("No items extracted")
        recommendations.append("Check if the website has the requested content")
    
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
    
    return {
        'success': items_extracted > 0,
        'items_extracted': items_extracted,
        'quality_score': quality_score,
        'ai_response_length': len(extraction_result.get('ai_response', '')),
        'issues': issues
    }

def test_website(url: str, website_type: str, requirements: str) -> EvaluationResult:
    session_id = f"eval_{int(time.time())}"
    create_conversation_session(session_id)
    
    try:
        analysis_result = analyze_website(session_id, url)
        
        if not analysis_result['success']:
            return EvaluationResult(
                url=url,
                website_type=website_type,
                scraping_method="failed",
                content_length=0,
                structured_data_count=0,
                images_found=0,
                links_found=0,
                pages_scraped=0,
                extraction_success=False,
                items_extracted=0,
                issues=["Analysis failed"],
                recommendations=["Check URL accessibility"]
            )
        
        extraction_result = extract_data_with_requirements(session_id, requirements)
        
        scraping_eval = evaluate_scraping_quality(analysis_result.get('analysis', {}))
        extraction_eval = evaluate_extraction_quality(extraction_result.get('data', {}))
        
        issues = []
        recommendations = []
        
        if scraping_eval['quality_score'] < 20:
            issues.append("Low content quality")
            recommendations.append("Consider using advanced scraping methods")
        
        if extraction_eval['items_extracted'] == 0:
            issues.append("No data extracted")
            recommendations.append("Review extraction requirements")
        
        issues.extend(extraction_eval['issues'])
        recommendations.extend(extraction_eval['recommendations'])
        
        return EvaluationResult(
            url=url,
            website_type=website_type,
            scraping_method=analysis_result.get('analysis', {}).get('extraction_method', 'unknown'),
            content_length=scraping_eval['content_length'],
            structured_data_count=scraping_eval['structured_data_count'],
            images_found=scraping_eval['images_found'],
            links_found=scraping_eval['links_found'],
            pages_scraped=scraping_eval['pages_scraped'],
            extraction_success=extraction_eval['success'],
            items_extracted=extraction_eval['items_extracted'],
            issues=issues,
            recommendations=recommendations
        )
        
    except Exception as e:
        return EvaluationResult(
            url=url,
            website_type=website_type,
            scraping_method="error",
            content_length=0,
            structured_data_count=0,
            images_found=0,
            links_found=0,
            pages_scraped=0,
            extraction_success=False,
            items_extracted=0,
            issues=[f"Error: {str(e)}"],
            recommendations=["Check system configuration"]
        )

class ScrapingEvaluator:
    def __init__(self):
        self.test_urls = [
            ("https://www.amazon.com", "ecommerce", "Extract products with titles, prices, and images"),
            ("https://www.lemonde.fr", "news", "Extract articles with titles, dates, and summaries"),
            ("https://www.github.com", "platform", "Extract repositories with names, descriptions, and stats"),
            ("https://www.medium.com", "blog", "Extract articles with titles, authors, and reading times"),
            ("https://www.reddit.com", "social", "Extract posts with titles, scores, and comments")
        ]
    
    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        results = []
        
        for url, website_type, requirements in self.test_urls:
            time.sleep(2)
            result = test_website(url, website_type, requirements)
            results.append(result)
        
        total_tests = len(results)
        successful_scrapes = sum(1 for r in results if r.content_length > 0)
        successful_extractions = sum(1 for r in results if r.extraction_success)
        advanced_scrapes = sum(1 for r in results if r.scraping_method == "advanced")
        
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
        
        report = {
            "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "successful_scrapes": successful_scrapes,
            "successful_extractions": successful_extractions,
            "advanced_scrapes": advanced_scrapes,
            "results": [
                {
                    "url": r.url,
                    "website_type": r.website_type,
                    "scraping_method": r.scraping_method,
                    "content_length": r.content_length,
                    "structured_data_count": r.structured_data_count,
                    "images_found": r.images_found,
                    "links_found": r.links_found,
                    "pages_scraped": r.pages_scraped,
                    "extraction_success": r.extraction_success,
                    "items_extracted": r.items_extracted,
                    "issues": r.issues,
                    "recommendations": r.recommendations
                }
                for r in results
            ],
            "common_issues": issue_counts,
            "recommendations": recommendation_counts
        }
        
        report_path = Path("scraping_evaluation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report

if __name__ == "__main__":
    evaluator = ScrapingEvaluator()
    report = evaluator.run_comprehensive_evaluation() 