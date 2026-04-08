import 'package:dio/dio.dart';

class ApiClient {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));

  Future<Map<String, dynamic>> infer(List<Map<String, double>> landmarks) async {
    final response = await _dio.post('/infer', data: {'landmarks': landmarks});
    return response.data as Map<String, dynamic>;
  }
}
