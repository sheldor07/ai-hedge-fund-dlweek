import logging
from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Optional, Any, Union
from .mongo_client import get_db_client
from .schema import Task, StockAnalysis, TradeDecision, Report
from ..config import settings

logger = logging.getLogger(settings.APP_NAME)

def _convert_id(item):
    if item and "_id" in item:
        item["id"] = str(item["_id"])
        del item["_id"]
    return item

class TaskOperations:
    @staticmethod
    def create_task(task: Task) -> Task:
        db = get_db_client()
        task_dict = task.dict(exclude={"id"})
        
        result = db.tasks.insert_one(task_dict)
        task.id = str(result.inserted_id)
        
        logger.info(f"Created task {task.id} of type {task.type} for {task.stock_symbol}")
        return task
    
    @staticmethod
    def get_task(task_id: str) -> Optional[Task]:
        db = get_db_client()
        task_dict = db.tasks.find_one({"_id": ObjectId(task_id)})
        
        if not task_dict:
            return None
        
        task_dict = _convert_id(task_dict)
        return Task(**task_dict)
    
    @staticmethod
    def update_task_status(task_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None) -> Optional[Task]:
        db = get_db_client()
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        
        if status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now()
        
        if result:
            update_data["result"] = result
            
        if error:
            update_data["error"] = error
        
        db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
        
        return TaskOperations.get_task(task_id)
    
    @staticmethod
    def get_pending_tasks(limit: int = 10) -> List[Task]:
        db = get_db_client()
        tasks = list(db.tasks.find(
            {"status": "pending"},
            sort=[("created_at", 1)],
            limit=limit
        ))
        
        return [Task(**_convert_id(task)) for task in tasks]

class AnalysisOperations:
    @staticmethod
    def create_analysis(analysis: StockAnalysis) -> StockAnalysis:
        db = get_db_client()
        analysis_dict = analysis.dict(exclude={"id"})
        
        result = db.stock_analyses.insert_one(analysis_dict)
        analysis.id = str(result.inserted_id)
        
        logger.info(f"Created analysis {analysis.id} for {analysis.stock_symbol}")
        return analysis
    
    @staticmethod
    def get_analysis(analysis_id: str) -> Optional[StockAnalysis]:
        db = get_db_client()
        analysis_dict = db.stock_analyses.find_one({"_id": ObjectId(analysis_id)})
        
        if not analysis_dict:
            return None
        
        analysis_dict = _convert_id(analysis_dict)
        return StockAnalysis(**analysis_dict)
    
    @staticmethod
    def update_analysis(analysis_id: str, update_data: Dict[str, Any]) -> Optional[StockAnalysis]:
        db = get_db_client()
        update_data["updated_at"] = datetime.now()
        
        db.stock_analyses.update_one(
            {"_id": ObjectId(analysis_id)},
            {"$set": update_data}
        )
        
        return AnalysisOperations.get_analysis(analysis_id)
    
    @staticmethod
    def get_latest_analysis(stock_symbol: str, analysis_type: str) -> Optional[StockAnalysis]:
        db = get_db_client()
        analysis_dict = db.stock_analyses.find_one(
            {"stock_symbol": stock_symbol, "analysis_type": analysis_type},
            sort=[("created_at", -1)]
        )
        
        if not analysis_dict:
            return None
        
        analysis_dict = _convert_id(analysis_dict)
        return StockAnalysis(**analysis_dict)

class DecisionOperations:
    @staticmethod
    def create_decision(decision: TradeDecision) -> TradeDecision:
        db = get_db_client()
        decision_dict = decision.dict(exclude={"id"})
        
        result = db.trade_decisions.insert_one(decision_dict)
        decision.id = str(result.inserted_id)
        
        logger.info(f"Created trade decision {decision.id} for {decision.stock_symbol}: {decision.recommendation}")
        return decision
    
    @staticmethod
    def get_decision(decision_id: str) -> Optional[TradeDecision]:
        db = get_db_client()
        decision_dict = db.trade_decisions.find_one({"_id": ObjectId(decision_id)})
        
        if not decision_dict:
            return None
        
        decision_dict = _convert_id(decision_dict)
        return TradeDecision(**decision_dict)
    
    @staticmethod
    def get_latest_decision(stock_symbol: str) -> Optional[TradeDecision]:
        db = get_db_client()
        decision_dict = db.trade_decisions.find_one(
            {"stock_symbol": stock_symbol},
            sort=[("created_at", -1)]
        )
        
        if not decision_dict:
            return None
        
        decision_dict = _convert_id(decision_dict)
        return TradeDecision(**decision_dict)

class ReportOperations:
    @staticmethod
    def create_report(report: Report) -> Report:
        db = get_db_client()
        report_dict = report.dict(exclude={"id"})
        
        result = db.reports.insert_one(report_dict)
        report.id = str(result.inserted_id)
        
        logger.info(f"Created report {report.id} for {report.stock_symbol}")
        return report
    
    @staticmethod
    def get_report(report_id: str) -> Optional[Report]:
        db = get_db_client()
        report_dict = db.reports.find_one({"_id": ObjectId(report_id)})
        
        if not report_dict:
            return None
        
        report_dict = _convert_id(report_dict)
        return Report(**report_dict)
    
    @staticmethod
    def get_report_by_analysis(analysis_id: str) -> Optional[Report]:
        db = get_db_client()
        report_dict = db.reports.find_one({"analysis_id": analysis_id})
        
        if not report_dict:
            return None
        
        report_dict = _convert_id(report_dict)
        return Report(**report_dict)